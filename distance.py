"""
-------------------------------------------
-    Author: Asadullah Dal                -
-    =============================        -
-    Company Name: AiPhile                -
-    =============================        -
-    Purpose : Youtube Channel            -
-    ============================         -
-    Link: https://youtube.com/c/aiphile  -
-------------------------------------------
"""

import cv2  # Importing OpenCV library for computer vision tasks
import pyttsx3  # Importing pyttsx3 library for text-to-speech

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Known variables for distance estimation
KNOWN_DISTANCE = 76.2  # Distance from the camera to the object in centimeters
KNOWN_WIDTH = 14.3     # Actual width of the object (face) in centimeters

# Color definitions for drawing on the video frame
GREEN = (0, 255, 0)  # RGB color for green
RED = (0, 0, 255)    # RGB color for red
WHITE = (255, 255, 255)  # RGB color for white
fonts = cv2.FONT_HERSHEY_COMPLEX  # Font style for text on images

# Initialize the video capture object with camera index 1
cap = cv2.VideoCapture(1)

# Load the pre-trained face detection model (Haar Cascade)
face_detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")


# Function to calculate the focal length of the camera
def focal_length(measured_distance, real_width, width_in_rf_image):
    """
    Calculates the focal length using the measured distance, real width of the object,
    and the width of the object in the reference image.
    :param measured_distance: Distance from the object to the camera.
    :param real_width: Actual width of the object in real life.
    :param width_in_rf_image: Width of the object in the reference image.
    :return: Focal length value.
    """
    focal_length_value = (width_in_rf_image * measured_distance) / real_width
    return focal_length_value


# Function to estimate the distance from the object to the camera
def distance_finder(focal_length, real_face_width, face_width_in_frame):
    """
    Estimates the distance between the camera and the object using the focal length,
    the real width of the object, and the width of the object in the current frame.
    :param focal_length: The focal length calculated previously.
    :param real_face_width: Actual width of the face.
    :param face_width_in_frame: Width of the face detected in the current frame.
    :return: Estimated distance.
    """
    distance = (real_face_width * focal_length) / face_width_in_frame
    return distance


# Function to detect face and get its width in pixels
def face_data(image):
    """
    Detects the face in the image and returns the width of the face in pixels.
    :param image: The image/frame in which to detect the face.
    :return: Width of the face in pixels.
    """
    face_width = 0  # Initialize face width to zero
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert image to grayscale
    faces = face_detector.detectMultiScale(gray_image, 1.3, 5)  # Detect faces in the image
    for (x, y, h, w) in faces:  # Loop through detected faces
        # Draw a rectangle around the face
        cv2.rectangle(image, (x, y), (x + w, y + h), WHITE, 1)
        face_width = w  # Set face width to the detected face's width

    return face_width  # Return the face width


# Function to make the system speak a message
def speak_message(message):
    """
    Uses text-to-speech to speak a given message.
    :param message: The message to be spoken.
    """
    engine.say(message)
    engine.runAndWait()


# Read the reference image from the directory
ref_image = cv2.imread("Ref_image.png")

# Get the face width in the reference image
ref_image_face_width = face_data(ref_image)

# Calculate the focal length using the reference image
focal_length_found = focal_length(KNOWN_DISTANCE, KNOWN_WIDTH, ref_image_face_width)
print(f"Calculated Focal Length: {focal_length_found}")  # Print the found focal length
cv2.imshow("ref_image", ref_image)  # Display the reference image

# Main loop to read video frames and estimate distance
while True:
    _, frame = cap.read()  # Read a frame from the camera

    # Get the width of the face in the current frame
    face_width_in_frame = face_data(frame)
    
    # If a face is detected, calculate the distance
    if face_width_in_frame != 0:
        # Estimate the distance using the calculated focal length and known width
        Distance = distance_finder(focal_length_found, KNOWN_WIDTH, face_width_in_frame)
        
        # Print the estimated distance to the console
        print(f"Estimated Distance: {round(Distance, 2)} CM")
        
        # Display the estimated distance on the video frame
        cv2.putText(
            frame, f"Distance = {round(Distance, 2)} CM", (50, 50), fonts, 1, WHITE, 2
        )
        
        # Check if the distance is between 100 cm and 90 cm and speak the message if true
        if 90 <= Distance <= 100:
            speak_message("Intruder at 95 cm")
    
    # Show the video frame with the distance annotation
    cv2.imshow("frame", frame)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord("q"):
        break

# Release the video capture and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
