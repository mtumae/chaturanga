from fastapi import FastAPI

app = FastAPI(title="FastAPI Service")


@app.get("/")
def read_root():
    return {"status": "online", "message": "FastAPI is running inside Docker"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
