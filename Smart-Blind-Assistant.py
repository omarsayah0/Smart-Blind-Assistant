import cv2
import pyttsx3
import time
from ultralytics import YOLO
import numpy as np

engine = pyttsx3.init()
engine.setProperty('rate', 140)
engine.setProperty('volume', 1.0)

import threading

def speak(text):
    threading.Thread(target=_speak_in_background, args=(text,)).start()

def _speak_in_background(text):
    engine.say(text)
    engine.runAndWait()

model = YOLO("yolov8n.pt")
model.conf = 0.4
model.iou = 0.5 

def distance(box_width, frame_width):

    ratio = box_width / frame_width
    if ratio < 0.3:
        return "far"
    else:
        return "close"

def check_traffic_light_color(frame, box):

    x1, y1, x2, y2 = map(int, box)
    traffic = frame[y1:y2, x1:x2]

    hsv = cv2.cvtColor(traffic, cv2.COLOR_BGR2HSV)

    red_lower1 = np.array([0, 70, 50])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 70, 50])
    red_upper2 = np.array([180, 255, 255])

    red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
    red_mask = red_mask1 + red_mask2
    red_pixels = np.sum(red_mask > 0)


    green_lower = np.array([36, 70, 70])
    green_upper = np.array([89, 255, 255])
    green_mask = cv2.inRange(hsv, green_lower, green_upper)
    green_pixels = np.sum(green_mask > 0)

    orange_lower = np.array([11, 100, 100])
    orange_upper = np.array([25, 255, 255])
    orange_mask = cv2.inRange(hsv, orange_lower, orange_upper)
    orange_pixels = np.sum(orange_mask > 0)
    
    if red_pixels > green_pixels and red_pixels > orange_pixels:
        return "red"
    elif green_pixels > red_pixels and green_pixels > orange_pixels:
        return "green"
    elif orange_pixels > red_pixels and orange_pixels > green_pixels:
        return "orange"
    else:
        return "unknown"

def main():
    cap = cv2.VideoCapture("video.mp4")
    last_spoken_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_height, frame_width = frame.shape[:2]

        results = model.predict(frame, verbose=False)
        
 
        detections = results[0].boxes  

        traffic_light_info = []
        vehicles_info = []
        frame_center_y = frame_height // 2 #not used not, but maybe in a future edit

        for box in detections:
            cls_id = int(box.cls[0].item())
            conf = box.conf[0].item() #not used not, but maybe in a future edit
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            class_name = model.names[cls_id]

            if class_name in ["car", "truck", "motorcycle", "bus"]:
                box_w = x2 - x1
                dist_text = distance(box_w, frame_width)
                vehicles_info.append((class_name, dist_text))

            elif class_name == "traffic light":
                color = check_traffic_light_color(frame, [x1, y1, x2, y2])
                traffic_light_info.append(color)


        current_time = time.time()
        time_diff = current_time - last_spoken_time
        speak_interval = 5.0

        if time_diff > speak_interval:
            if "red" in traffic_light_info:
                speak("wait , the trafic is red")
                last_spoken_time = current_time
            elif "orange" in traffic_light_info:
                speak("get ready , its orange")
            elif "green" in traffic_light_info:
                speak_interval = 8.0
                close_vehicles = [v for v in vehicles_info if v[1] == "close"]
                if len(close_vehicles) > 0:
                    speak("wait , the traffic is green but a car is close")
                else:
                    speak("you can walk , the trafic is green ")
                last_spoken_time = current_time

        annotated_frame = results[0].plot()
        cv2.imshow("Smart Blind Assistant", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
