from ultralytics import YOLO
import torch

def main():
    # 1. Load the starter brain (Small version for better Pi performance later)
    model = YOLO('yolov8s.pt') 

    # 2. Start Training
    # We use 'device=0' for your NVIDIA GPU. If it fails, change to 'cpu'.
    model.train(
        data='data.yaml',
        epochs=100,         # 100 turns of studying
        imgsz=640,          # Standard high-res training
        batch=16,           # Processing 16 images at a time
        device='cpu',           # Use your RTX 4060 GPU
        name='EcoPoints_Model'
    )

if __name__ == '__main__':
    main()