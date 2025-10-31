import os
from pathlib import Path
import boto3
import torch
from PIL import Image
from torchvision import transforms

class PlantDiseaseModel:
    def __init__(self):
        self.model = None
        self.model_path = os.getenv("mlops_project/src/app/models/floracare_model_fast.pth")
        self.s3_bucket = os.getenv("S3_BUCKET_NAME")
        self.s3_key = os.getenv("S3_MODEL_KEY")
        self.device = torch.device("cpu")
        self.transform = transforms.Compose([
            transforms.Resize((224,224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
        ])

    def download_model_from_s3(self):
        if not self.s3_bucket or not self.s3_key:
            raise ValueError("S3_BUCKET_NAME and S3_MODEL_KEY env vars must be set")
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading model s3://{self.s3_bucket}/{self.s3_key} -> {self.model_path}")
        s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION"))
        s3.download_file(self.s3_bucket, self.s3_key, self.model_path)
        print("Download complete")

    def load_model(self):
        if not Path(self.model_path).exists():
            self.download_model_from_s3()
        # load checkpoint for CPU (adapt to how you saved model state)
        checkpoint = torch.load(self.model_path, map_location=self.device)
        # If you saved model.state_dict(), adapt this to instantiate model and load_state_dict
        # Example pseudo:
        model = checkpoint.get("model") if isinstance(checkpoint, dict) else None
        if model is None:
            # assume saved state_dict
            from torchvision.models import resnet18
            net = resnet18(num_classes=38)  # adjust classes
            net.load_state_dict(checkpoint)
            net.eval()
            self.model = net.to(self.device)
        else:
            self.model = model.eval().to(self.device)
        print("Model loaded")

    def predict(self, pil_image: Image.Image):
        img = self.transform(pil_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(img)
            probs = torch.nn.functional.softmax(logits, dim=1)
            top_prob, top_idx = torch.max(probs, dim=1)
            return int(top_idx.item()), float(top_prob.item())
