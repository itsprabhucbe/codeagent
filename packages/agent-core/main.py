import uvicorn
from fastapi import FastAPI

app = FastAPI(title="CodeAgent API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
