import cv2
import os
import time
from ultralytics import YOLO

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, 'models', 'best.pt')
    
    print(f"Loading YOLO model from: {model_path}")
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Error loading model! Make sure best.pt is in the models/ folder. Error: {e}")
        return

    print("Starting Webcam via picamera2...")
    try:
        from picamera2 import Picamera2
        cam = Picamera2()
        config = cam.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
        cam.configure(config)
        cam.start()
        use_picam2 = True
    except ImportError:
        print("picamera2 not found. Falling back to cv2.VideoCapture(0)...")
        cam = cv2.VideoCapture(0)
        use_picam2 = False

    print("Camera started! Press 'q' to stop.")

    while True:
        if use_picam2:
            frame = cam.capture_array()
            ret = frame is not None
        else:
            ret, frame = cam.read()
            
        if not ret:
            print("Failed to grab frame from camera.")
            break
            
        # Rotate 180 since camera is typically upside down on the RVM
        frame = cv2.rotate(frame, cv2.ROTATE_180)
        
        # Run inference! conf=0.5 means only show boxes if 50% sure.
        results = model.predict(frame, conf=0.5, verbose=False)

        # Draw the results onto the frame
        annotated_frame = results[0].plot()

        # Display the frame
        cv2.imshow("EcoPoints Local Camera Test", annotated_frame)

        # Quit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if use_picam2:
        cam.stop()
        cam.close()
    else:
        cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
