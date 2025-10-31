# ~/quick_server.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from PIL import Image
from io import BytesIO
import uvicorn
import torch
from torchvision import transforms
from torchvision.models import resnet18

MODEL_PATH = "/tmp/floracare_model_fast.pth"
NUM_CLASSES = 38

# load model (reuse the same heuristic as above)
def load_model():
    ckpt = torch.load(MODEL_PATH, map_location="cpu")
    if not isinstance(ckpt, dict):
        try:
            ckpt.eval()
            return ckpt
        except Exception:
            # fallback to state_dict
            state = ckpt
    else:
        if 'state_dict' in ckpt:
            state = ckpt['state_dict']
        elif 'model_state_dict' in ckpt:
            state = ckpt['model_state_dict']
        elif 'model' in ckpt and hasattr(ckpt['model'], 'eval'):
            return ckpt['model']
        else:
            state = ckpt

    # create resnet fallback
    model = resnet18(num_classes=NUM_CLASSES)
    new_state = {}
    for k, v in state.items():
        new_key = k.replace("module.", "") if k.startswith("module.") else k
        new_state[new_key] = v
    model.load_state_dict(new_state, strict=False)
    model.eval()
    return model

MODEL = load_model()
print("Model loaded into memory:", type(MODEL))

app = FastAPI()

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    try:
        b = await image.read()
        img = Image.open(BytesIO(b)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")
    x = transform(img).unsqueeze(0)
    with torch.no_grad():
        out = MODEL(x)
        probs = torch.nn.functional.softmax(out, dim=1)
        top_prob, top_idx = torch.max(probs, dim=1)
    return {"class_idx": int(top_idx.item()), "confidence": float(top_prob.item())}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
