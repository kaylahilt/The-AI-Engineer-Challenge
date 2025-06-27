"""
Minimal FastAPI app for testing Vercel deployment
"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "Simple app is working"}

@app.post("/api/test")
def test(data: dict):
    return {"received": data, "status": "success"}

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 