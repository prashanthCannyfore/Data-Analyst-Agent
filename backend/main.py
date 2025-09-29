import os
import pandas as pd
import io
import json
import re
import requests
import base64
import matplotlib.pyplot as plt
from io import StringIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from fastapi.middleware.cors import CORSMiddleware


# === Load environment variables ===
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not set in .env file.")
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# === Initialize Gemini LLM ===
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

# === FastAPI app ===
app = FastAPI(title="Data Analyst Agent")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev/testing, allow all. In prod, specify your frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Configure Logging ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_url(text: str) -> str | None:
    match = re.search(r'(https?://[^\s]+)', text)
    return match.group(0) if match else None

def scrape_data_from_url(url: str) -> pd.DataFrame | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))
        logger.info(f"Found {len(tables)} tables")

        if not tables:
            return None

        for idx, table in enumerate(tables):
            if isinstance(table.columns, pd.MultiIndex):
                table.columns = [' '.join(str(c) for c in col).strip() for col in table.columns]
            else:
                table.columns = [str(c) for c in table.columns]

            logger.info(f"Using table #{idx} with columns: {table.columns.tolist()}")

            lower_cols = [c.lower() for c in table.columns]
            if ("rank" in lower_cols or "#" in lower_cols or "weeks at number one" in lower_cols or "weeks at number one 2020" in lower_cols) and \
               ("peak" in lower_cols or "weeks at number one" in lower_cols or "weeks at number one 2020" in lower_cols):
                if not table.empty:
                    return table

        if not tables[0].empty:
            return tables[0]
    except Exception as e:
        logger.exception("Scraping error")
    return None

def generate_scatterplot(df: pd.DataFrame) -> str | None:
    try:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [' '.join(str(c) for c in col).strip() for col in df.columns]

        logger.info(f"Available columns for plot: {df.columns.tolist()}")

        possible_x = [col for col in df.columns if 'rank' in col.lower() or '#' in col.lower() or 'position' in col.lower()]
        possible_y = [col for col in df.columns if 'peak' in col.lower() or 'weeks at number' in col.lower()]

        if not possible_x or not possible_y:
            raise ValueError("No suitable columns for scatterplot.")

        x_col = possible_x[0]
        y_col = possible_y[0]

        logger.info(f"Plotting: x='{x_col}' vs y='{y_col}'")

        df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        df_clean = df.dropna(subset=[x_col, y_col])

        plt.figure(figsize=(8, 6))
        plt.scatter(df_clean[x_col], df_clean[y_col], color='blue', label=f"{x_col} vs {y_col}")
        plt.plot(df_clean[x_col], df_clean[y_col], linestyle='--', color='red', label="Trend")
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        plt.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        img = base64.b64encode(buf.read()).decode('utf-8')
        return f"data:image/png;base64,{img}"
    except Exception as e:
        logger.exception("Plot generation failed")
        return None

@app.post("/api/")
async def data_analyst_agent(
    questions_txt: UploadFile = File(...),
    data_csv: UploadFile | None = File(default=None),
    data_json: UploadFile | None = File(default=None)
):
    start_time = time.time()

    try:
        questions_text = (await questions_txt.read()).decode("utf-8")
        logger.info("Received questions")

        url = extract_url(questions_text)
        df_from_url = scrape_data_from_url(url) if url else None
        logger.info(f"Scraped df from URL: {url is not None}")

        df_from_upload = None
        if data_csv:
            try:
                df_from_upload = pd.read_csv(io.BytesIO(await data_csv.read()))
                logger.info("Loaded CSV upload")
            except Exception:
                logger.exception("Error reading CSV")
                raise HTTPException(status_code=400, detail="Invalid CSV file format.")
        elif data_json:
            try:
                df_from_upload = pd.read_json(io.BytesIO(await data_json.read()))
                logger.info("Loaded JSON upload")
            except Exception:
                logger.exception("Error reading JSON")
                raise HTTPException(status_code=400, detail="Invalid JSON file format.")

        # ✅ Avoid ambiguous truth value
        df = None
        if df_from_upload is not None:
            df = df_from_upload
        elif df_from_url is not None:
            df = df_from_url

        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="No data available.")

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [' '.join(str(c) for c in col).strip() for col in df.columns]

        try:
            import tabulate
            data_preview = tabulate.tabulate(df.head(5), headers='keys', tablefmt='pipe', showindex=False)
        except ImportError:
            data_preview = df.head(5).to_csv(index=False)

        prompt = f"""
You are a helpful data analyst assistant.

Answer the following questions using the provided data sample. 
Return your answers as a JSON array or object. 
**Return ONLY raw JSON. DO NOT include explanations, markdown code blocks, or anything else.**

User Questions:
{questions_text}

Data Sample:
{data_preview}

If a plot is requested, just say: "Plot will be generated separately."  
"""

        logger.info("Prompt ready")

        llm_response = None
        with ThreadPoolExecutor() as executor:
            for attempt in range(3):
                try:
                    logger.info(f"Attempt {attempt+1} to invoke LLM")
                    llm_future = executor.submit(lambda: llm.invoke(prompt))
                    rem = 300 - (time.time() - start_time)
                    timeout_for_call = min(rem, 300)
                    llm_response = llm_future.result(timeout=timeout_for_call)
                    logger.info("LLM responded")
                    break
                except FutureTimeoutError:
                    logger.warning("LLM invocation timed out on this attempt")
                    if attempt == 2:
                        raise HTTPException(status_code=500, detail="LLM invocation timed out after retries")
                    time.sleep(5)
                except Exception:
                    logger.exception("LLM invocation error")
                    raise HTTPException(status_code=500, detail="LLM invocation failed")

        content = llm_response.content if hasattr(llm_response, "content") else str(llm_response)

        # ✅ Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").strip()
        if content.endswith("```"):
            content = content[:-3].strip()

        try:
            answers = json.loads(content)
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            answers = {"raw_response": content}

        plot_uri = None
        try:
            if "scatterplot" in questions_text.lower():
                plot_uri = generate_scatterplot(df)
                if plot_uri:
            # If answers is a dict, look for the "plot will be generated separately" and replace
                    if isinstance(answers, dict):
                        for k in answers:
                            if isinstance(answers[k], str) and "plot will be generated separately" in answers[k].lower():
                                answers[k] = plot_uri
                                break
            # If answers is a list, scan each item and update if applicable
                    elif isinstance(answers, list):
                        for i, item in enumerate(answers):
                            if isinstance(item, str) and "plot will be generated separately" in item.lower():
                                answers[i] = plot_uri
                                break
        except Exception:
            logger.exception("Scatterplot generation failed")


        elapsed = time.time() - start_time
        if elapsed > 300:
            logger.error("Overall request exceeded 5 minutes")
            raise HTTPException(status_code=500, detail="Timeout exceeded")

        return JSONResponse(content=answers)

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Unhandled error in API")
        raise HTTPException(status_code=500, detail=str(e))
