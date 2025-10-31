# --- START: S3-in-memory model loading and /predict endpoint ---
# Add these imports near top of file (or where appropriate)
from fastapi import UploadFile, File, HTTPException
from fastapi import status
from fastapi import BackgroundTasks
import os, io, traceback, importlib
from PIL import Image

# late imports for heavy libs so app can still start without them until needed
try:
    import boto3
except Exception:
    boto3 = None

try:
    import torch
    import torchvision.transforms as T
except Exception:
    torch = None
    T = None

# Config (set these env vars on EC2; default placeholders provided)
S3_BUCKET = os.getenv("MODEL_S3_BUCKET", "your-bucket-name")
S3_KEY    = os.getenv("MODEL_S3_KEY", "models/floracare_model_fast.pth")
# If your .pth is a state_dict, set MODEL_CLASS_PATH like "src.app.models.my_model:MyModel"
MODEL_CLASS_PATH = os.getenv("MODEL_CLASS_PATH", "")  # optional; if empty and .pth is state_dict -> error
# If your model class requires args, you'll need to edit the code below to pass them.

DEVICE = torch.device("cuda" if torch and torch.cuda.is_available() else "cpu") if torch else None

# In-memory cached model or state_dict
_LOADED_MODEL = None
_LOADED_STATE_DICT = None

def download_s3_bytes(bucket: str, key: str) -> bytes:
    if boto3 is None:
        raise RuntimeError("boto3 is not installed in the environment.")
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj["Body"].read()
    return data

def import_class_from_path(class_path: str):
    """
    class_path format: "package.module:ClassName"
    Example: "src.app.models.my_model:MyModel"
    """
    if ":" not in class_path:
        raise ValueError("MODEL_CLASS_PATH expected format 'module.path:ClassName'")
    module_path, class_name = class_path.split(":", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls

def load_model_from_s3_into_memory(bucket=S3_BUCKET, key=S3_KEY):
    """
    Downloads model bytes from S3 and attempts to load it.
    - If bytes load to a torch.nn.Module (saved object) -> use it.
    - If load returns a dict (state_dict) and MODEL_CLASS_PATH is provided -> instantiate and load.
    - Otherwise raise informative error.
    """
    global _LOADED_MODEL, _LOADED_STATE_DICT
    if _LOADED_MODEL is not None:
        return _LOADED_MODEL

    if torch is None:
        raise RuntimeError("torch is not available in this environment")

    # Download bytes
    try:
        data = download_s3_bytes(bucket, key)
    except Exception as e:
        raise RuntimeError(f"Failed to download model from s3://{bucket}/{key}: {e}")

    bio = io.BytesIO(data)
    try:
        # attempt torch.load directly from buffer
        obj = torch.load(bio, map_location=DEVICE)
    except Exception as e:
        # helpful error with limited trace
        raise RuntimeError(f"torch.load failed for model bytes: {e}\n{traceback.format_exc()}")

    # If it's a dict -> likely a state_dict
    if isinstance(obj, dict):
        _LOADED_STATE_DICT = obj
        # If user provided a class path, try to instantiate and load state_dict
        if MODEL_CLASS_PATH:
            try:
                cls = import_class_from_path(MODEL_CLASS_PATH)
                # NOTE: If your model class needs constructor args (num_classes, etc),
                # change the following instantiation accordingly.
                model = cls()  # <-- modify here if constructor needs args
                model.load_state_dict(_LOADED_STATE_DICT)
                model.to(DEVICE)
                model.eval()
                _LOADED_MODEL = model
                return _LOADED_MODEL
            except Exception as e:
                raise RuntimeError(f"Loaded state_dict but failed to instantiate/load model class from MODEL_CLASS_PATH='{MODEL_CLASS_PATH}': {e}\n{traceback.format_exc()}")
        else:
            raise RuntimeError("Model loaded from S3 is a state_dict (dict). Set MODEL_CLASS_PATH env var to the module:ClassName for the model class or modify code to instantiate the model before loading state_dict.")
    else:
        # assume it's a saved model object (torch.nn.Module)
        try:
            model = obj
            model.to(DEVICE)
            model.eval()
            _LOADED_MODEL = model
            return _LOADED_MODEL
        except Exception as e:
            raise RuntimeError(f"Loaded object from .pth but failed to prepare as model: {e}\n{traceback.format_exc()}")

# Provide an async startup hook to load the model so first request is fast (optional)
from fastapi import FastAPI

@app.on_event("startup")
async def startup_load_model():
    try:
        # Try to load model into memory (this will throw helpful errors if fails)
        load_model_from_s3_into_memory()
        print(f"[startup] Model loaded from s3://{S3_BUCKET}/{S3_KEY}")
    except Exception as e:
        # Do not crash the entire app — log so you can inspect, but startup continues
        print(f"[startup] Warning: model failed to load from S3 at startup: {e}")

# Preprocess (adjust to training pipeline)
def get_preprocess():
    if T is None:
        raise RuntimeError("torchvision.transforms not available")
    return T.Compose([
        T.Resize((224,224)),
        T.ToTensor(),
        T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])

@app.post("/predict", tags=["Inference"])
async def predict(file: UploadFile = File(...)):
    # Ensure torch exists
    if torch is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="torch is not available on this server")

    # Read uploaded bytes
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image upload: {e}")

    # Load (or get cached) model
    try:
        model = _LOADED_MODEL if _LOADED_MODEL is not None else load_model_from_s3_into_memory()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model from S3: {e}")

    # Preprocess + infer
    try:
        preprocess = get_preprocess()
        x = preprocess(img).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            out = model(x)
            if isinstance(out, (list, tuple)):
                out = out[0]
            probs = torch.nn.functional.softmax(out, dim=1).cpu().numpy().tolist()
            pred = int(torch.argmax(out, dim=1).cpu().numpy()[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}\n{traceback.format_exc()}")

    return {"status": "ok", "prediction": pred, "probs": probs}
# --- END: S3-in-memory model loading and /predict endpoint ---
