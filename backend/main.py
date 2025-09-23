from fastapi import FastAPI
from routers import analysis

app = FastAPI()

# Include the analysis routes
app.include_router(analysis.router, prefix="/api")
