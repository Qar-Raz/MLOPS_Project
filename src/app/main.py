import io
import time
from typing import List

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

# Prometheus metrics helper functions and instruments
# (You must have src/app/monitoring/metrics.py in your repo)
from src.app.monitoring.metrics import (
    export_metrics,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    IN_PROGRESS,
    TOKENS_TOTAL,
)

# =====================================================
# 1. FASTAPI APP METADATA
# =====================================================

app = FastAPI(
    title="MLOps Project API",
    description="Plant disease classifier API with Prometheus metrics",
    version="0.1.0",
)


# =====================================================
# 2. DEVICE SETUP (CPU/GPU) & MODEL LOADING
# =====================================================

# Use GPU if available, else CPU. This is standard practice in FastAPI+PyTorch
# production examples today. :contentReference[oaicite:5]{index=5}
# Attach the instrumentation middleware from the slide
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# We will rebuild the same ResNet18 architecture that was trained.
# This matches how you trained it: load a pretrained resnet18, replace final fc,
# then load your saved weights. This is the typical way to serve PyTorch
# transfer learning models in FastAPI. :contentReference[oaicite:6]{index=6}
NUM_CLASSES = 38  # adjust if your real class count is different
MODEL_WEIGHTS_PATH = "src/app/models/floracare_model_fast.pth"
CLASS_NAMES_PATH = "src/app/models/class_names.txt"

# Create the same model definition
model = models.resnet18(weights="IMAGENET1K_V1")
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, NUM_CLASSES)

# Load trained weights
try:
    state_dict = torch.load(MODEL_WEIGHTS_PATH, map_location=device)
    model.load_state_dict(state_dict)
except Exception as e:
    # If you hit this in dev, you haven't mounted/copy'd floracare_model.pth
    # into the container. In production guides, this is where they'd log
    # and maybe raise 500. :contentReference[oaicite:7]{index=7}
    print(f"[WARN] Could not load model weights: {e}")

model = model.to(device)
model.eval()  # VERY IMPORTANT: no dropout / no batchnorm updates

# Load class names so we can map predicted index -> disease label
# This is standard for image classifiers served via API. :contentReference[oaicite:8]{index=8}
try:
    with open(CLASS_NAMES_PATH, "r") as f:
        CLASS_NAMES: List[str] = [line.strip() for line in f if line.strip()]
except Exception as e:
    print(f"[WARN] Could not load class names file: {e}")
    # Fallback: numbered labels
    CLASS_NAMES = [f"class_{i}" for i in range(NUM_CLASSES)]


# =====================================================
# 3. IMAGE TRANSFORMS (MATCH TRAINING PREPROCESS)
# =====================================================

# These MUST match what you used during validation in training:
# Resize(256) -> CenterCrop(224) -> ToTensor() -> Normalize(...)
# This is literally the standard ImageNet-style preprocessing pipeline that
# transfer-learning ResNet18 expects. :contentReference[oaicite:9]{index=9}
inference_transform = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


def prepare_image(image_bytes: bytes) -> torch.Tensor:
    """
    Load raw bytes -> PIL.Image -> apply inference_transform -> add batch dim -> device
    """
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    tensor = inference_transform(pil_img).unsqueeze(0)  # [1, 3, 224, 224]
    return tensor.to(device)


# =====================================================
# 4. BASIC PING ENDPOINTS
# =====================================================


@app.get("/", tags=["General"])
def read_root():
    """
    Simple sanity endpoint. Good for demo and health checks.
    FastAPI auto-generates docs at /docs which is commonly used
    to test ML inference endpoints interactively. :contentReference[oaicite:10]{index=10}
    """
    return {"message": "Welcome to the Plant Disease Classifier API (MLOps Project)"}


@app.get("/health", tags=["General"])
def health_check():
    """
    For Docker HEALTHCHECK and uptime checks.
    """
    return {"status": "ok"}


# =====================================================
# 5. /metrics ENDPOINT FOR PROMETHEUS
# =====================================================


@app.get("/metrics", tags=["Monitoring"])
def metrics_endpoint():
    """
    Prometheus scrapes this endpoint.
    We return Prometheus exposition text format using prometheus_client.
    This pattern (FastAPI exposing /metrics, Prometheus scraping it, Grafana
    graphing it) is standard in modern FastAPI observability setups. :contentReference[oaicite:11]{index=11}
    """
    body, content_type = export_metrics()
    return Response(content=body, media_type=content_type)


# =====================================================
# 6. REQUEST SCHEMA + INFERENCE ENDPOINT
# =====================================================


class PredictResponse(BaseModel):
    predicted_class: str
    predicted_index: int
    confidence: float  # softmax prob of that class
    tokens_used: int  # we expose this for Prometheus, similar to usage metrics


@app.post("/predict", response_model=PredictResponse, tags=["Model"])
async def predict(request: Request, file: UploadFile = File(...)):
    """
    1. Read uploaded image
    2. Preprocess to tensor
    3. Run model forward pass (no grad)
    4. Convert logits -> predicted class + confidence
    5. Update Prometheus metrics:
       - REQUEST_COUNT (Counter)
       - REQUEST_LATENCY (Histogram)
       - IN_PROGRESS (Gauge)
       - TOKENS_TOTAL (Counter)
    6. Return JSON response with class label

    This matches how current production-ish examples deploy PyTorch models
    behind FastAPI: you accept an image (or JSON), transform, run model.eval(),
    and respond with class label + probability. Then you expose /metrics for
    Prometheus to scrape. :contentReference[oaicite:12]{index=12}
    """

    # mark request start
    start_time = time.perf_counter()
    IN_PROGRESS.inc()

    try:
        # Safety: ensure we actually got a file
        if file is None:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Read file bytes
        img_bytes = await file.read()

        # "tokens_used" for an image doesn't totally make sense like NLP tokens,
        # but we still log *something* to demonstrate custom Prometheus counters.
        # We'll treat "tokens_used" as image size in KB.
        tokens_used = max(1, len(img_bytes) // 1024)

        # Preprocess
        batch_tensor = prepare_image(img_bytes)

        # Inference
        with torch.no_grad():
            outputs = model(batch_tensor)  # shape [1, NUM_CLASSES]
            probs = torch.softmax(outputs, dim=1)  # convert to probabilities
            conf, pred_idx_tensor = torch.max(probs, 1)
            pred_idx = int(pred_idx_tensor.item())
            conf_val = float(conf.item())

        # Map index -> human class name
        predicted_label = (
            CLASS_NAMES[pred_idx]
            if pred_idx < len(CLASS_NAMES)
            else f"class_{pred_idx}"
        )

        # Update metrics AFTER successful inference
        REQUEST_COUNT.inc()  # total number of /predict calls
        TOKENS_TOTAL.inc(tokens_used)  # custom usage counter
        elapsed = time.perf_counter() - start_time
        REQUEST_LATENCY.observe(elapsed)  # histogram of latencies

        # Build structured response for client
        return PredictResponse(
            predicted_class=predicted_label,
            predicted_index=pred_idx,
            confidence=conf_val,
            tokens_used=tokens_used,
        )

    finally:
        # always decrement in-progress gauge
        IN_PROGRESS.dec()
