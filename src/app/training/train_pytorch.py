import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
import mlflow
import mlflow.pytorch
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
DATA_DIR = os.getenv('DATA_DIR', 'data/raw/plantvillage')
BATCH_SIZE = 32
LEARNING_RATE = 0.001
NUM_EPOCHS = 10
NUM_CLASSES = 38
MODEL_SAVE_PATH = "models/saved/plantmd_resnet18.pth"

# MLflow setup
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("PlantMD_PyTorch_Training")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Data transforms
data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# Load datasets
image_datasets = {x: datasets.ImageFolder(os.path.join(DATA_DIR, x), data_transforms[x])
                  for x in ['train', 'val']}
dataloaders = {x: DataLoader(image_datasets[x], batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
               for x in ['train', 'val']}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
class_names = image_datasets['train'].classes

print(f"Found {len(class_names)} classes")

# Start MLflow run
with mlflow.start_run(run_name="ResNet18_PlantDisease"):
    # Log parameters
    mlflow.log_params({
        "model": "ResNet18",
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "num_epochs": NUM_EPOCHS,
        "num_classes": NUM_CLASSES,
        "optimizer": "SGD",
        "device": str(device)
    })
    
    # Load pre-trained model
    model = models.resnet18(weights='IMAGENET1K_V1')
    for param in model.parameters():
        param.requires_grad = False
    
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, NUM_CLASSES)
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.fc.parameters(), lr=LEARNING_RATE, momentum=0.9)
    
    best_acc = 0.0
    
    # Training loop
    for epoch in range(NUM_EPOCHS):
        print(f'Epoch {epoch+1}/{NUM_EPOCHS}')
        
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()
            
            running_loss = 0.0
            running_corrects = 0
            
            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)
                optimizer.zero_grad()
                
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            
            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]
            
            # Log metrics to MLflow
            mlflow.log_metrics({
                f"{phase}_loss": epoch_loss,
                f"{phase}_accuracy": epoch_acc.item()
            }, step=epoch)
            
            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')
            
            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'num_classes': NUM_CLASSES
    }, MODEL_SAVE_PATH)
    
    # Log model to MLflow
    mlflow.pytorch.log_model(model, "model")
    mlflow.log_artifact(MODEL_SAVE_PATH)
    
    # Log best accuracy
    mlflow.log_metric("best_val_accuracy", best_acc.item())
    
    print(f"Training finished. Best validation accuracy: {best_acc:.4f}")
    print(f"Model saved to {MODEL_SAVE_PATH}")