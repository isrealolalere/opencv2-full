from flask import Flask, render_template, Response, request, redirect, url_for
import cv2
from win32com.client import Dispatch
import pyttsx3
import time
import threading

app = Flask(__name__)

# Initialize video capture with a default IP (can be changed by user)
camera_ip = ""

# Initialize video capture (change the index if necessary to match your camera)
cap = cv2.VideoCapture(camera_ip)

# Known variables for distance estimation
KNOWN_DISTANCE = 76.2  # Measured distance to object in centimeters
KNOWN_WIDTH = 14.3     # Known width of the object in centimeters
fonts = cv2.FONT_HERSHEY_COMPLEX

# Global variables for distance settings
last_speech_time = 0    # Tracks the last time a speech alert was triggered
speech_interval = 5     # Time interval in seconds between consecutive speech alerts
alert_distance_min = 50 # Default minimum alert distance (in cm)
alert_distance_max = 70 # Default maximum alert distance (in cm)

def focal_length(measured_distance, real_width, width_in_rf_image):
    focal_length_value = (width_in_rf_image * measured_distance) / real_width
    print(f"[DEBUG] Calculated focal length: {focal_length_value}")
    return focal_length_value

def distance_finder(focal_length, real_face_width, face_width_in_frame):
    distance = (real_face_width * focal_length) / face_width_in_frame
    print(f"[DEBUG] Calculated distance: {distance} cm")
    return distance

def face_data(image):
    face_width = 0
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)

    for (x, y, h, w) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 255), 1)
        face_width = w
        print(f"[DEBUG] Detected face width: {face_width}")

    return face_width

# def speak_message(message):
#     print(f"[INFO] Speaking message: {message}")
#     speak = Dispatch("SAPI.SpVoice")
#     speak.Speak(message)

def speak_message(message):
    print(f"[INFO] Speaking message: {message}")
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()

def generate_frames():
    focal_length_found = focal_length(KNOWN_DISTANCE, KNOWN_WIDTH, 100)
    global last_speech_time
    while True:
        success, frame = cap.read()
        if not success:
            print("[ERROR] Failed to read frame from camera.")
            break

        face_width_in_frame = face_data(frame)
        if face_width_in_frame != 0:
            Distance = distance_finder(focal_length_found, KNOWN_WIDTH, face_width_in_frame)
            current_time = time.time()
            if alert_distance_min <= Distance <= alert_distance_max and (current_time - last_speech_time) > speech_interval:
                print(f"[ALERT] Intruder detected at {round(Distance, 2)} cm.")
                threading.Thread(target=speak_message, args=(f"Intruder at {round(Distance, 2)} cm..",)).start()
                last_speech_time = current_time
            
            cv2.putText(frame, f"Distance = {round(Distance, 2)} CM", (50, 50), fonts, 1, (255, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """
    Render the main page with video feed and distance setting form.
    """
    # Initial render without any message
    return render_template('index4.html', min_distance=alert_distance_min, max_distance=alert_distance_max, message='', camera_ip=camera_ip)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_distance', methods=['POST'])
def set_distance():
    """
    Handle the form submission to set alert distances and provide feedback to the user.
    """
    global alert_distance_min, alert_distance_max
    message = ''  # Initialize message variable
    try:
        min_distance = int(request.form['min_distance'])
        max_distance = int(request.form['max_distance'])

        # Validate the inputs to ensure minimum is less than maximum
        if min_distance >= max_distance:
            message = "Minimum distance must be less than maximum distance."
            print(f"[ERROR] {message}")
        else:
            alert_distance_min = min_distance
            alert_distance_max = max_distance
            message = f"Updated alert distances: Min = {alert_distance_min} cm, Max = {alert_distance_max} cm"
            print(f"[INFO] {message}")
    except ValueError:
        message = "Invalid distance value entered. Please enter valid integers."
        print(f"[ERROR] {message}")

    # Return to the main page with the message
    return render_template('index.html', min_distance=alert_distance_min, max_distance=alert_distance_max, message=message, camera_ip=camera_ip)

@app.route('/set_camera_ip', methods=['POST'])
def set_camera_ip():
    """
    Handle the form submission to set the camera IP address.
    """
    global camera_ip, cap
    message = ''  # Initialize message variable
    try:
        new_ip = request.form['camera_ip']
        # Set the new camera IP and update the VideoCapture object
        camera_ip = new_ip
        cap.release()  # Release any existing capture
        cap = cv2.VideoCapture(camera_ip)
        message = f"Updated camera IP address to: {camera_ip}"
        print(f"[INFO] {message}")
    except Exception as e:
        message = f"Error setting camera IP: {str(e)}"
        print(f"[ERROR] {message}")

    # Return to the main page with the message
    return render_template('index4.html', min_distance=alert_distance_min, max_distance=alert_distance_max, message=message, camera_ip=camera_ip)

if __name__ == '__main__':
    print("[INFO] Starting Flask server...")
    app.run(host='0.0.0.0', port=5000)
