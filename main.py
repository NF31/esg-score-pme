from fastapi import FastAPI

app = FastAPI(title="ESG Score PME")


@app.get("/health")
def health():
    return {"status": "ok"}
