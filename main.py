from fastapi import FastAPI

app = FastAPI(title="Chaturanga")


@app.get("/")
def read_root():
    return {"status": "online", "message": "FastAPI is running."}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
