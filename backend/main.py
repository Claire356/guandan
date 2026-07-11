from fastapi import FastAPI

app = FastAPI(title="AI掼蛋训练 API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
