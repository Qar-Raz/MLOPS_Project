from fastapi import FastAPI

app = FastAPI(
    title="MLOps Project API",
    description="API for the MLOps Milestone 1 project.",
    version="0.1.0",
)

@app.get("/", tags=["General"])
def read_root():
    """A general endpoint that returns a welcome message."""
    return {"message": "Welcome to our MLOps API!"}

@app.get("/health", tags=["General"])
def health_check():
    """
    Health check endpoint.
    This is required by the Dockerfile's HEALTHCHECK instruction.
    It returns a 200 OK status to confirm the API is running.
    """
    return {"status": "ok"}