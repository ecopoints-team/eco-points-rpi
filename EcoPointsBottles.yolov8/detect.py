import cv2
from ultralytics import YOLO

# 1. Load the SPECIFIC brain we just trained
model_path = r'EcoPointsBottles.yolov8\runs\detect\EcoPoints_Model-2\weights\best.pt'
model = YOLO(model_path)

# 2. Open Laptop Webcam
cap = cv2.VideoCapture(0)

print("Starting Webcam... Press 'q' to stop.")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 3. Predict! 
    # conf=0.5: Don't show boxes unless the AI is 50% sure.
    results = model(frame, conf=0.5)

    # 4. Draw the results using YOLO's built-in tool (Easier than the manual loop!)
    annotated_frame = results[0].plot()

    # 5. Display
    cv2.imshow("EcoPoints Local Test", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()