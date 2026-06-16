from ultralytics import YOLO

def main():
    # Load a pre-trained YOLOv8 model
    model = YOLO('/home/ecopoints/System Program/yolov8s.pt')  # You can choose 'yolov8s', 'yolov8m', 'yolov8l', 'yolov8x' as well

    # Train the model using GPU 1
    results = model.train(
        data='/home/ecopoints/System Program/EcoPoints.v1-roboflow-instant-1--eval-.yolov8/data.yaml',  # Path to your data.yaml file
        epochs=100,        # Number of epochs
        batch=16,          # Batch size
        imgsz=640,         # Image size
        device='cpu',      # Use GPU 1 (NVIDIA GeForce RTX 4060 Laptop GPU)
        workers=12,        # Number of worker threads
        name='yolov8_custom_train'  # Name of the training run
    )
    
if __name__ == '__main__':
    main()
    
# import torch
# print(torch.cuda.is_available())  # Should return True
# print(torch.cuda.get_device_name(0))