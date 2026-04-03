from fastapi import FastAPI

app = FastAPI(title="Logic Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "logic-service"}


@app.get("/logic/ping")
def logic_ping():
    return {"message": "logic service running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
