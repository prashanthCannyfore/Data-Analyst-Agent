import os
import io
import traceback
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

router = APIRouter()

@router.post("/analyze")
async def analyze_data(
    task: str = Form(...),
    files: list[UploadFile] = File(None)
):
    try:
        dfs = {}
        if files:
            for file in files:
                content = await file.read()
                if file.filename.endswith(".csv"):
                    dfs[file.filename] = pd.read_csv(io.BytesIO(content))
                elif file.filename.endswith((".xls", ".xlsx")):
                    dfs[file.filename] = pd.read_excel(io.BytesIO(content))

        # Prepare schema preview for Gemini
        schema_info = "\n".join(
            [f"{name}: {df.head(3).to_dict()}" for name, df in dfs.items()]
        ) if dfs else "No datasets uploaded."

        # Ask Gemini to generate Pandas code
        prompt = f"""
        You are a Python data analyst.
        User request: {task}

        Available datasets:
        {schema_info}

        Write Python (pandas, matplotlib if needed) code that solves the task.
        Only return code, no explanations.
        """

        response = model.generate_content(prompt)
        code = response.text.strip("` \npython")

        # Execute safely
        local_env = {"pd": pd, "dfs": dfs}
        exec(code, {}, local_env)

        # Collect DataFrame outputs
        results = {}
        for k, v in local_env.items():
            if isinstance(v, pd.DataFrame):
                results[k] = v.head(20).to_dict(orient="records")

        return JSONResponse({
            "task": task,
            "code": code,
            "results": results
        })

    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)
