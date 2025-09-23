import pandas as pd
import io
from urllib.request import urlopen

def read_data_from_csv(file_content: bytes) -> pd.DataFrame:
    """Reads a CSV file from raw bytes content and returns a DataFrame."""
    try:
        df = pd.read_csv(io.BytesIO(file_content))
        return df
    except Exception as e:
        return f"Error reading CSV: {e}"

def read_data_from_url(url: str) -> pd.DataFrame:
    """Reads data from a URL and returns a DataFrame. Supports CSV or HTML tables."""
    try:
        if url.endswith(".csv"):
            df = pd.read_csv(url)
        else:
            # Assumes it's an HTML page with tables
            tables = pd.read_html(url)
            # You might need logic here to select the correct table
            df = tables[0] 
        return df
    except Exception as e:
        return f"Error reading data from URL: {e}"