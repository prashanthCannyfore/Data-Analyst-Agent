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

## Example: film task (curl)
curl -X POST "http://127.0.0.1:8000/api/" \
 -F "questions=@questions.txt" 

# where questions.txt contains the film prompt:
# Scrape the list of highest grossing films from Wikipedia. It is at the URL:
# https://en.wikipedia.org/wiki/List_of_highest-grossing_films
# Answer the following questions and respond with a JSON array of strings containing the answer.
# 1. How many $2 bn movies were released before 2000?
# 2. Which is the earliest film that grossed over $1.5 bn?
# 3. What's the correlation between the Rank and Peak?
# 4. Draw a scatterplot of Rank and Peak along with a dotted red regression line through it.
#    Return as a base-64 encoded data URI under 100000 bytes.

## Example: attach a CSV for an ad-hoc dataset
curl -X POST "http://127.0.0.1:8000/api/" \
 -F "questions=@questions.txt" \
 -F "files=@data.csv"
