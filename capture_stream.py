from flask import Flask, Response
from picamera2 import Picamera2
import cv2
from libcamera import Transform
import numpy as np


#Parameters
id = 0
font = cv2.FONT_HERSHEY_COMPLEX
height=1
boxColor=(0,0,255)      #BGR- GREEN
nameColor=(255,255,255) #BGR- WHITE
confColor=(255,255,0)   #BGR- TEAL
face_detector=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

app = Flask(__name__)

camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}, transform=Transform(vflip=True)))
camera.start()

def generate_frames():
    while True:
        frame = camera.capture_array()
        # Convert frame from BGR to grayscale
        frameGray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Create a DS faces- array with 4 elements- x,y coordinates top-left corner), width and height
        faces = face_detector.detectMultiScale(
            frameGray,      # The grayscale frame to detect
            scaleFactor=1.10,# How much the image size is reduced at each image scale-10% reduction
            minNeighbors=4, # How many neighbors each candidate rectangle should have to retain it
            minSize=(40, 40) # Minimum possible object size. Objects smaller than this size are ignored.
            #maxSize=(30, 30) # Maximum possible object size. Objects larger than this size are ignored.
        )


        for (x, y, w, h) in faces:
            # Create a bounding box across the detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), boxColor, 3) # 5 parameters - frame, topleftcoords, bottomrightcoords, boxcolor, thickness
        
	# Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        # Use yield to create a generator
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
