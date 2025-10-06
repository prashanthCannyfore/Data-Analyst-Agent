from io import StringIO, BytesIO
import os
import re
import json
import base64
import time
import logging
import duckdb
import requests
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Optional
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from bs4 import BeautifulSoup
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("data-analyst-agent")

EMBED_DIR = "./embedding_store"
os.makedirs(EMBED_DIR, exist_ok=True)
DUCKDB_PATH = os.path.join(EMBED_DIR, "embeddings.duckdb")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY environment variable not set")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

app = FastAPI(title="Data Analyst Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

con = duckdb.connect(DUCKDB_PATH)
con.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        chunk_id INTEGER,
        text STRING,
        vector BLOB
    )
""")

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_gemini_response(text: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)

def call_gemini_with_retry(prompt, retries=3, delay=60):
    for attempt in range(1, retries + 1):
        try:
            response = model.generate_content(prompt)
            content = response.text.strip()
            if not content:
                raise ValueError("Empty Gemini response.")
            return content
        except Exception as e:
            logger.warning(f"Gemini error: {e}")
            if attempt == retries:
                raise
            time.sleep(delay)
            delay *= 2

def extract_url(text: str) -> Optional[str]:
    match = re.search(r"(https?://[^\s]+)", text)
    return match.group(1) if match else None

def scrape_page_all_data(url: str) -> tuple[str, list[pd.DataFrame]]:
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "iframe", "img"]):
            tag.decompose()
        texts = [el.get_text(strip=True) for el in soup.find_all(['p', 'h1', 'h2', 'li', 'td', 'th']) if el.get_text(strip=True)]
        tables = pd.read_html(response.text)
        return "\n".join(texts), tables
    except Exception as e:
        logger.warning(f"Scraping failed: {e}")
        return "", []


def analyze_image_with_gemini(image: Image.Image) -> str:
    try:
        buf = BytesIO()
        image.save(buf, format="PNG")
        buf.seek(0)
        image_bytes = buf.read()
        image_data = {"mime_type": "image/png", "data": image_bytes}
        gemini_input = [image_data, "Describe this image in one sentence."]
        response = model.generate_content(gemini_input)
        return response.text.strip()
    except Exception as e:
        logger.warning(f"Gemini image analysis failed: {e}")
        return "Could not analyze image."

def execute_plot_code(code: str, tables: dict) -> str:
    try:
        local_vars = tables.copy()
        exec_globals = {"plt": plt, "pd": pd, "BytesIO": BytesIO, "base64": base64}
        plt.clf()
        exec(code, exec_globals, local_vars)

        if "image_base64" in local_vars:
            return local_vars["image_base64"]

        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=150)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logger.warning(f"Plot code failed: {e}")
        return "data:image/png;base64,"

def extract_text_chunks_from_dfs(df_list: list[pd.DataFrame]) -> list[str]:
    chunks = []
    for idx, df in enumerate(df_list):
        for i, row in df.iterrows():
            text = " | ".join([f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])])
            if text.strip():
                chunks.append(text)
    return chunks

def embed_and_store(chunks: list[str]):
    if not chunks:
        return
    embeddings = embedding_model.encode(chunks, convert_to_numpy=True)
    embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12

    con.execute("DELETE FROM embeddings")
    for i, vec in enumerate(embeddings):
        vec_bytes = vec.astype(np.float32).tobytes()
        con.execute("INSERT INTO embeddings VALUES (?, ?, ?)", (i, chunks[i], vec_bytes))

def search_similar_chunks(question: str, top_k: int = 5) -> list[str]:
    query_emb = embedding_model.encode([question], convert_to_numpy=True)[0]
    query_emb /= np.linalg.norm(query_emb) + 1e-12

    results = con.execute("SELECT chunk_id, text, vector FROM embeddings").fetchall()
    scores = []
    for chunk_id, text, vec_blob in results:
        vec = np.frombuffer(vec_blob, dtype=np.float32)
        sim = float(np.dot(query_emb, vec))
        scores.append((text, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [text for text, _ in scores[:top_k]]

@app.post("/api/")
async def data_analyst_agent(
    questions: UploadFile = File(...),
    data: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None)
):
    start = time.time()

    try:
        question_text = (await questions.read()).decode("utf-8")
        url = extract_url(question_text)
        conn = duckdb.connect(database=":memory:")
        all_tables = {}
        scraped_tables = []
        all_text = ""

        if url:
            all_text, dfs = scrape_page_all_data(url)
            scraped_tables = dfs[:3]
            for idx, df in enumerate(scraped_tables):
                conn.register(f"table_{idx}", df)
                all_tables[f"table_{idx}"] = df

        if data:
            try:
                contents = await data.read()
                csv_text = contents.decode("utf-8")
                print("=== CSV Contents ===")
                print(csv_text)
                df_csv = pd.read_csv(StringIO(csv_text))
                conn.register("csv_data", df_csv)
                all_tables["csv_data"] = df_csv
                scraped_tables.append(df_csv)
            except Exception as e:
                logger.warning(f"CSV error: {e}")
                return JSONResponse(content=["unknown", "CSV error", 0.0, "data:image/png;base64,"])
    
        if not scraped_tables:
            return JSONResponse(content=["unknown", "No data found", 0.0, "data:image/png;base64,"])

        chunks = extract_text_chunks_from_dfs(scraped_tables)
        embed_and_store(chunks)
        relevant_chunks = search_similar_chunks(question_text, top_k=5)

        data_summary = "\n".join([f"- {chunk}" for chunk in relevant_chunks])
        context_text = all_text[:2000]

        image_description = ""
        if image:
            image_obj = Image.open(image.file)
            image_description = analyze_image_with_gemini(image_obj)

        prompt = f"""
You are a professional data analyst assistant.

Answer the user's data-related question based on the provided information.
Your response must be a valid JSON object. Return only JSON — no text outside of it.

### Input Details:

- User Question:
{question_text}

- Data Chunks (filtered from scraped or uploaded data):
{data_summary}


- Image Description:
{image_description if image_description else "No description available."}

- Page Text (for context, if scraped from URL):
{context_text}

---

### Response Format (strict):

Return a single JSON object using only these allowed keys:

- "answer": (string) → A short sentence directly answering the question.
- "details": (optional, string) → Add reasoning or context here.
- "confidence": (optional, float) → A value between 0 and 1.
- "plot_code": (optional, string) → Python code to generate a plot using matplotlib, referencing tables like df, table_0, etc.

Important constraints:
- DO NOT return any base64 image data.
- DO NOT include actual plot images or previews.
- DO NOT wrap JSON in markdown code blocks.
- DO NOT return the plot as string. Only return plot_code if a plot is necessary.

Example (valid):

{{  
  "answer": "The Titanic dataset shows that survival rate was higher for females.",
  "confidence": 0.91,
  "plot_code": "plt.figure(figsize=(8,6)); df['Sex'].value_counts().plot(kind='bar'); plt.title('Gender Distribution')"
}}
"""

        logger.info("Calling Gemini...")
        response_text = call_gemini_with_retry(prompt)

        try:
            cleaned = clean_gemini_response(response_text)
            parsed_response = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Decode Error: {e}")
            logger.debug(f"Raw Gemini Output: {response_text}")
            return JSONResponse(content={"answer": "unknown", "details": "Gemini returned malformed JSON."})

        plot_code = parsed_response.get("plot_code", "")
        if plot_code and ("plt" in plot_code or "image_base64" in plot_code):
            parsed_response["plot_code"] = execute_plot_code(plot_code, all_tables)

        logger.info(f"Done in {time.time() - start:.2f} seconds")

        response_content = {k: v for k, v in parsed_response.items() if v is not None and v != ""}

        return JSONResponse(content=response_content)

    except Exception as e:
        logger.exception("Fatal error")
        return JSONResponse(content=["unknown", "Unhandled error", 0.0, "data:image/png;base64,"])
