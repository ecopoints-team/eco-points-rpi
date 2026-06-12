import cv2
import os
from ultralytics import YOLO

def main():
    # Construct the absolute path to the model in the models folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'models', 'best.pt')
    
    print(f"Loading YOLO model from: {model_path}")
    
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Error loading model! Make sure best.pt is in the models/ folder. Error: {e}")
        return

    # Open the default camera (0 for laptop webcam or Raspberry Pi camera)
    cap = cv2.VideoCapture(0)

    print("Starting Webcam... Press 'q' to stop.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame from camera.")
            break
        
        # Run inference! conf=0.5 means only show boxes if 50% sure.
        results = model(frame, conf=0.5)

        # Draw the results onto the frame
        annotated_frame = results[0].plot()

        # Display the frame
        cv2.imshow("EcoPoints Local Camera Test", annotated_frame)

        # Quit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
