import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
import os

# --- 1. Configuration & Hyperparameters ---

# Path to your dataset
# Assumes a folder structure like:
# data/
#   train/
#     class_a/
#       1.jpg
#       2.jpg
#     class_b/
#       ...
#   val/
#     class_a/
#       ...
#     class_b/
#       ...
DATA_DIR = "/Users/abdullah/Desktop/New Plant Diseases Dataset(Augmented)" # IMPORTANT: Change this to your dataset path

# Training settings
BATCH_SIZE = 32
LEARNING_RATE = 0.001
NUM_EPOCHS = 10 # Start with 10, increase if needed
NUM_CLASSES = 38 # IMPORTANT: Change this to the number of classes (disease categories) in your dataset

# Device configuration (use GPU if available, otherwise CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


# --- 2. Data Loading and Preprocessing ---

# Define transformations for the training and validation sets
# Data augmentation is applied to the training set to make the model more robust
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

# Create datasets and dataloaders
image_datasets = {x: datasets.ImageFolder(os.path.join(DATA_DIR, x), data_transforms[x])
                  for x in ['train', 'val']}
dataloaders = {x: DataLoader(image_datasets[x], batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
               for x in ['train', 'val']}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
class_names = image_datasets['train'].classes

print(f"Found {len(class_names)} classes: {class_names}")


# --- 3. Model Definition (Transfer Learning) ---

# Load a pre-trained ResNet-18 model
model = models.resnet18(weights='IMAGENET1K_V1')

# Freeze all the layers in the pre-trained model
for param in model.parameters():
    param.requires_grad = False

# Replace the final fully connected layer (the "classifier")
# with a new one for our specific number of classes.
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, NUM_CLASSES)

# Move the model to the configured device (GPU or CPU)
model = model.to(device)


# --- 4. Training the Model ---

# Define the loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.fc.parameters(), lr=LEARNING_RATE, momentum=0.9) # Only train the new classifier layer

print("Starting training...")

for epoch in range(NUM_EPOCHS):
    print(f'Epoch {epoch+1}/{NUM_EPOCHS}')
    print('-' * 10)

    # Each epoch has a training and validation phase
    for phase in ['train', 'val']:
        if phase == 'train':
            model.train()  # Set model to training mode
        else:
            model.eval()   # Set model to evaluate mode

        running_loss = 0.0
        running_corrects = 0

        # Iterate over data
        for inputs, labels in dataloaders[phase]:
            inputs = inputs.to(device)
            labels = labels.to(device)

            # Zero the parameter gradients
            optimizer.zero_grad()

            # Forward pass
            # Track history only if in training phase
            with torch.set_grad_enabled(phase == 'train'):
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

                # Backward pass + optimize only if in training phase
                if phase == 'train':
                    loss.backward()
                    optimizer.step()

            # Statistics
            running_loss += loss.item() * inputs.size(0)
            running_corrects += torch.sum(preds == labels.data)

        epoch_loss = running_loss / dataset_sizes[phase]
        epoch_acc = running_corrects.double() / dataset_sizes[phase]

        print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

print("Training finished.")

# --- 5. Save the Trained Model ---

# Save the model's state dictionary
MODEL_SAVE_PATH = "floracare_model.pth"
torch.save(model.state_dict(), MODEL_SAVE_PATH)
print(f"Model saved to {MODEL_SAVE_PATH}")
