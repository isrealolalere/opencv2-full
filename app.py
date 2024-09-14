from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)

def get_camera_index():
    try:
        with open('camera_index.txt', 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        print("[ERROR] Camera index file not found.")
        return 0
    except ValueError:
        print("[ERROR] Invalid camera index in file.")
        return 0

# Initialize video capture with the selected camera index
def initialize_camera():
    camera_index = get_camera_index()
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise Exception(f"Failed to open camera {camera_index}.")
    return cap

cap = initialize_camera()

@app.route('/')
def index():
    return render_template('index3.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            print("[ERROR] Failed to read frame from camera.")
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
