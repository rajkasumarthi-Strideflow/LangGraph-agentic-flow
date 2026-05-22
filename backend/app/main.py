from fastapi import FastAPI

app = FastAPI(
    title="WarrantyWise Agentic Support Platform",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "warrantywise-agentic-support",
        "version": "0.1.0",
    }