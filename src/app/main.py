from fastapi import FastAPI, Request
from fastapi.responses import Response
from pydantic import BaseModel

# import your metrics helpers
from src.app.monitoring.metrics import export_metrics, track_prediction

# (optional) import joblib if your teammate has the trained model artifact
# import joblib
# model = joblib.load("models/best_model.pkl")

app = FastAPI(
    title="MLOps Project API",
    description="API for the MLOps Milestone 1 project.",
    version="0.1.0",
)


class PredictRequest(BaseModel):
    text: str


@app.get("/", tags=["General"])
def read_root():
    return {"message": "Welcome to our MLOps API!"}


@app.get("/health", tags=["General"])
def health_check():
    return {"status": "ok"}


@app.get("/metrics", tags=["Monitoring"])
def metrics_endpoint():
    """
    Expose Prometheus metrics in the format Prometheus scrapes.
    This is the normal `/metrics` pattern in FastAPI+Prometheus setups,
    and Prometheus will scrape this on an interval to populate data that
    Grafana can visualize. :contentReference[oaicite:9]{index=9}
    """
    body, content_type = export_metrics()
    return Response(content=body, media_type=content_type)


@app.post("/predict", tags=["Model"])
async def predict(req: PredictRequest, request: Request):
    """
    /predict:
    - in final version, should run the ML model for sentiment/label
    - we wrap the real work with track_prediction() so metrics are recorded
    """

    # define the actual inference logic as a function so we can pass it
    # into track_prediction()
    async def do_infer():
        text = req.text

        # STUB LOGIC (replace with real model):
        # this dummy sentiment logic is just to let you test metrics.
        if (
            "love" in text.lower()
            or "great" in text.lower()
            or "awesome" in text.lower()
        ):
            predicted_label = "POSITIVE"
        else:
            predicted_label = "NEUTRAL"

        tokens_used = len(text.split())

        # if you load an actual sklearn pipeline with joblib,
        # you'd do:
        # predicted_label = model.predict([text])[0]
        # tokens_used = len(text.split())

        return {
            "label": predicted_label,
            "tokens_used": tokens_used,
        }

    result = await track_prediction(request, do_infer)
    return result
