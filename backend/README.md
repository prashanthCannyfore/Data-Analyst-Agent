# Data Analyst Agent (FastAPI)

## Setup (local)
1. Create virtualenv
   python -m venv venv
   venv\Scripts\activate   # Windows
   source venv/bin/activate  # macOS / Linux

2. Install dependencies:
   pip install -r requirements.txt

3. (Optional) Set GOOGLE_API_KEY in env if you want Gemini planner:
   Windows (cmd): set GOOGLE_API_KEY=your_key
   PowerShell: $env:GOOGLE_API_KEY="your_key"
   macOS/Linux: export GOOGLE_API_KEY="your_key"

4. Run:
   uvicorn app:app --reload --port 8000
# 🌐 Data Analyst Agent – Web Scraping & QnA with LLM + DuckDB

A **FastAPI backend** for dynamically analyzing web content. This project scrapes web pages, builds vector embeddings for semantic search, and answers user questions using **OpenRouter LLMs**. It also generates visualizations for numeric data, returning all results in structured **JSON responses**, including base64-encoded images.

Perfect for researchers, analysts, and developers who need to **interact with web data intelligently**.

---

## ✨ Features

- **🌐Web Scraping**

  - Extracts clean text and structured tables from any public URL.
  - Ignores irrelevant elements like `<script>`, `<style>`, `<img>`, `<svg>`, and `<i>`.

- **🗄️DuckDB Integration**

  - Stores extracted structured data (tables, text chunks) and generated embeddings for semantic search
  - Enables fast analytical queries without requiring external databases
  - Embeddings allow the LLM to efficiently retrieve relevant context for each question

- **🧠 LLM Integration (OpenRouter)**

  - Answers natural language questions based on scraped content.
  - Supports dynamic queries on both text and tabular data.

- **📊 Automatic Visualization**

  - Detects numeric queries and generates scatterplots automatically.
  - Returns images encoded in base64 for seamless frontend display.

- **🌍 CORS & Frontend Ready**
  - Supports cross-origin requests for frameworks like React, Next.js, or Vue.

---

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip 
- GOOGLE_API_KEY

### Installation

```bash
git clone  https://github.com/prashanthCannyfore/Data-Analyst-Agent.git
cd backemd
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

```

---

> Note: questions.txt file is required for all queries.

## Example Questions.txt file

```
Scrape the list of highest grossing films from Wikipedia. It is at the URL:
https://en.wikipedia.org/wiki/List_of_highest-grossing_films

Answer the following questions and respond with a JSON array of strings containing the answer.

1. How many $2 bn movies were released before 2000?
2. Which is the earliest film that grossed over $1.5 bn?
3. What's the correlation between the Rank and Peak?
4. Draw a scatterplot of Rank and Peak along with a dotted red regression line through it.
   Return as a base-64 encoded data URI, `"data:image/png;base64,iVBORw0KG..."` under 100,000 bytes.

```

## Get Your OpenRouter API Key

[Google api key [https://www.google.com/aclk?sa=L&ai=DChsSEwiF2uf4i6iQAxXcqmYCHTruM_MYACICCAEQARoCc20&ae=2&co=1&ase=2&gclid=EAIaIQobChMIhdrn-IuokAMV3KpmAh067jPzEAAYASABEgLODPD_BwE&cid=CAASrwHkaHt-sv77X3rCHizgDTzxYGdp1dNy2ibgQSBMS4mvT7-SmiOGgJ3sX_55Ftppn3WIUdpLL7gorUztb5tLZb3ytTOeuF5GxqlknTN0rYJ5FxAl5qBsmo5vp2wzL-Xq2O7eoToTAgwdzIQkyNiTjPaIM3npO_fHAjrMk2inpWiYVbJZWEYJ-EUfPa8O_9IZToXG_7q56G6C3-ZDeq5nQfwcGQK4O1meOn8g6IyZEcH-&cce=2&category=acrcp_v1_71&sig=AOD64_0AG-3nRKA_kotz2S0zXP-Vb6yGTQ&q&nis=4&adurl&ved=2ahUKEwjc3-L4i6iQAxXWRmwGHRncKHgQqyQoAHoECAsQDQ])

- Sign up and get your API key

---

## Example (Model/ApiKey)

```
Model = google/gemini-2.5-flash
Api_key ="AIzaSyC1yP9d6Z_ymeKpyTj8UE6O0znEHnT93s0"
```

## Testing the API with cURL

```bash
curl.exe -X POST `
  'https://blakely-estimative-nonarbitrarily.ngrok-free.dev/api/' `
  -H 'accept: application/json' `
  -H 'Content-Type: multipart/form-data' `
  -F 'questions=@questions.txt;type=text/plain' `
  -F 'data=@sales.csv;type=text/csv' `
  -F 'image=@Screenshot 2025-10-10 113427.png;type=image/png'

```

## Example JSON response

```
[answer":"1. One movie (Titanic) grossed over $2 billion before 2000. 2. The earliest film that grossed over $1.5 billion is Titanic (1997). 3. The correlation between Rank and Peak is approximately -0.41.","confidence":0.95,"plot_code":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABLAAAAOECAYAAACxbcj6AAAAOnRFWHRTb2Z0d2FyZQBNYXRwbG90bGliIHZlcnNpb24zLjEwL"]

```

# License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.  
© 2025 prashanth.
