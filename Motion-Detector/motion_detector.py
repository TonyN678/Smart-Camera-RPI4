from flask import Flask, Response, render_template
from picamera2 import Picamera2
import cv2
from libcamera import Transform
import numpy as np
import imutils
from datetime import datetime
import mail_notif

# =============================================================================
# USER-SET PARAMETERS
# =============================================================================

# Number of frames to pass before changing the frame to compare the current
# frame against
FRAMES_TO_PERSIST = 10

# Minimum boxed area for a detected motion to count as actual motion
# Use to filter out noise or small objects
# Decrease to increase sensitivity, suitable for far range detection
# Increase to detect short-range target(25000)
MIN_SIZE_FOR_MOVEMENT = 10000 

# Minimum length of time where no motion is detected it should take
#(in program cycles) for the program to declare that there is no movement
MOVEMENT_DETECTED_PERSISTENCE = 50

# Number of detection before declaring there is an actual movement,
# not external impacts like sunslight or thing falling down
COUNT_THRESHOLD_DETECTION = 30

# =============================================================================
# CORE PROGRAM
# ===============================================================

# Initiate Flask app
app = Flask(__name__)

# Initiate the Pi Camera with some settings
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}, transform=Transform(vflip=True)))
camera.start()

# Init frame variables
first_frame = None
next_frame = None

# Init display font and timeout counters
font = cv2.FONT_HERSHEY_SIMPLEX
delay_counter = 0
movement_persistent_counter = 0
count = 0
photo_number = 3
stream_photo_list = []   

def generate_frames():
    # Declare these variables as Global to avoid UnboundLocalError
    global count, first_frame, next_frame, delay_counter, movement_persistent_counter, photo_number, stream_photo_list

    while True:
        # Output frame(or picture) from Pi Camera to variable frame
        frame = camera.capture_array()

        # Set transient motion detected as false
        transient_movement_flag = False
        
        # Resize and save a greyscale version of the image
        frame = imutils.resize(frame, width = 750)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Blur it to remove camera noise (reducing false positives)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # If the first frame is nothing, initialise it
        if first_frame is None:
            first_frame = gray    

        delay_counter += 1

        # Otherwise, set the first frame to compare as the previous frame
        # But only if the counter reaches the appriopriate value
        # The delay is to allow relatively slow motions to be counted as large
        # motions if they're spread out far enough
        if delay_counter > FRAMES_TO_PERSIST:
            delay_counter = 0
            first_frame = next_frame

            
        # Set the next frame to compare (the current frame)
        next_frame = gray

        # Compare the two frames, find the difference
        frame_delta = cv2.absdiff(first_frame, next_frame)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

        # Fill in holes via dilate(), and find contours of the thesholds
        thresh = cv2.dilate(thresh, None, iterations = 2)
        cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # loop over the contours
        for c in cnts:
            global x, y, w, h
            # Save the coordinates of all found contours
            (x, y, w, h) = cv2.boundingRect(c)
            
            # If the contour is too small, ignore it, otherwise, there's transient
            # movement
            if cv2.contourArea(c) > MIN_SIZE_FOR_MOVEMENT:
                transient_movement_flag = True
                
                # Draw a rectangle around big enough movements
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                #print(f"Coordinate: ({x},{y})")

        # The moment something moves momentarily, reset the persistent
        # movement timer.
        if transient_movement_flag == True:
            movement_persistent_flag = True
            movement_persistent_counter = MOVEMENT_DETECTED_PERSISTENCE
            
            # number of movement observed before declaring there is actual movement
            count += 1
            if count > COUNT_THRESHOLD_DETECTION and photo_number >0:
                # Save photos and save it to a list
                camera.capture_file(f"/tmp/StreamPhoto{photo_number}.jpg")
                stream_photo_list.append(f"/tmp/StreamPhoto{photo_number}.jpg")
                print("Detected Motion")
                count = 0
                photo_number -= 1

            elif photo_number == 0:
                # send email to notify of movements
                mail_notif.envoie_mail(1, stream_photo_list)
                stream_photo_list.clear()
                photo_number = 3

        # As long as there was a recent transient movement, say a movement
        # was detected    
        if movement_persistent_counter > 0:
            text = "Movement Detected " + str(movement_persistent_counter)

        
            movement_persistent_counter -= 1
        else:
            text = "No Movement Detected"

        # Print the text on the screen, include datetime and movement status
        cv2.putText(frame, str(text), (10,35), font, 0.75, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(frame, datetime.now().strftime("%d/%m/%Y, %H:%M:%S"), (10, frame.shape[0] - 10), font, 0.50, (0, 0, 255), 1)      
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        
        frame = buffer.tobytes()
        # Use yield to create a generator
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port="5000")

