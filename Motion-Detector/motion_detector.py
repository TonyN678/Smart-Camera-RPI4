from flask import Flask, Response, render_template
from picamera2 import Picamera2
import cv2
from libcamera import Transform
import numpy as np
#import imutils
from datetime import datetime
import mail_notif
#from Pantilt_v2 import PanTiltCamera
import RPi.GPIO as GPIO
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
MIN_SIZE_FOR_MOVEMENT = 25000 

# Minimum length of time where no motion is detected it should take
#(in program cycles) for the program to declare that there is no movement
MOVEMENT_DETECTED_PERSISTENCE = 50

# Number of detection before declaring there is an actual movement,
# not external impacts like sunslight or thing falling down
COUNT_THRESHOLD_DETECTION = 30

# Number of photos sent through gmail for notification
PHOTO_NUMBER_SENT = 3
# =============================================================================
# CORE PROGRAM
# ===============================================================

# Initiate Flask app
app = Flask(__name__)

# Initiate the Pi Camera with some settings
camera = Picamera2()
camera.configure(camera.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}, transform=Transform(vflip=True)))
camera.start()

# Initiate PantTilt Mechanism
frame_width = 640
frame_height = 480
# Servo positions
pan_angle = 90  # Start at middle (90 degrees)
tilt_angle = 90
# Setup GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.OUT)  # Pan servo
GPIO.setup(8, GPIO.OUT)  # Tilt servo

# Set up PWM on GPIO pins for both servos
pan_pwm = GPIO.PWM(16, 50)  # 50Hz frequency
tilt_pwm = GPIO.PWM(8, 50)  # 50Hz frequency

# Start PWM with servos in middle position (7.5% duty cycle = 90°)
pan_pwm.start(7.5)
tilt_pwm.start(7.5)
def change_servo_duty_cycle(pwm, angle):
    # Convert angle (0°-180°) to duty cycle
    duty_cycle = 2.5 + (angle / 18.0)
    pwm.ChangeDutyCycle(duty_cycle)

# Init frame variables
first_frame = None
next_frame = None

# Init display font and timeout counters
font = cv2.FONT_HERSHEY_SIMPLEX
delay_counter = 0
movement_persistent_counter = 0
count = 0
photo_number = PHOTO_NUMBER_SENT
stream_photo_list = []   

def generate_frames():
    # Declare these variables as Global to avoid UnboundLocalError
    global count, first_frame, next_frame, delay_counter, movement_persistent_counter, photo_number, stream_photo_list

    global pan_angle, tilt_angle
    while True:
        # Output frame(or picture) from Pi Camera to variable frame
        frame = camera.capture_array()

        # Set transient motion detected as false
        transient_movement_flag = False
        
        # Convert to grayscale and blur for noise reduction
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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

        # Dilate the thresholded image to fill in holes
        thresh = cv2.dilate(thresh, None, iterations = 2)
        
        # Find contours of the motion(outlines of potential movement) 
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            (x, y, w, h) = cv2.boundingRect(largest_contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Get the center of the motion
            center_x = x + w // 2
            center_y = y + h // 2

            # Calculate pan and tilt adjustments
            frame_center_x = 640 // 2
            frame_center_y = 480 // 2
            pan_change = 0
            tilt_change = 0

            if center_x < frame_center_x - 50:
                pan_change = -5  # Move left
            elif center_x > frame_center_x + 50:
                pan_change = 5  # Move right

            if center_y < frame_center_y - 50:
                tilt_change = -5  # Move up
            elif center_y > frame_center_y + 50:
                tilt_change = 5  # Move down

            # Adjust servo angles (ensure they stay between 0 and 180 degrees)
            pan_angle = max(0, min(180, pan_angle + pan_change))
            tilt_angle = max(0, min(180, tilt_angle + tilt_change))

            # Change the duty cycle based on the new angles
            change_servo_duty_cycle(pan_pwm, pan_angle)
            change_servo_duty_cycle(tilt_pwm, tilt_angle)
#            # If the contour is too small, ignore it, otherwise, there's transient
#            # movement
#            if cv2.contourArea(c) > MIN_SIZE_FOR_MOVEMENT:
#                transient_movement_flag = True
#                radius = 8 
#                motion_center = (int(x + w/2), int(y + h/2))
#                # Draw a circle around the detected motion
#                cv2.circle(frame, motion_center, radius, (0, 255, 0), 2)
#            
#                print(motion_center)
#                x_coord = motion_center[0]
#                y_coord = motion_center[1]
#                camera_tracker.track_object(x_coord, y_coord)
                

        # The moment something moves momentarily, reset the persistent
        # movement timer.
        if transient_movement_flag == True:
            movement_persistent_flag = True
            movement_persistent_counter = MOVEMENT_DETECTED_PERSISTENCE
            
            # number of movement observed before declaring there is actual movement
          #  count += 1
          #  if count > COUNT_THRESHOLD_DETECTION and photo_number >0:
          #      # Save photos and save it to a list
          #      camera.capture_file(f"/tmp/StreamPhoto{photo_number}.jpg")
          #      stream_photo_list.append(f"/tmp/StreamPhoto{photo_number}.jpg")
          #      print("Detected Motion")
          #      count = 0
          #      photo_number -= 1

          #  elif photo_number == 0:
          #      # send email to notify of movements
          #      mail_notif.envoie_mail(1, stream_photo_list)
          #      stream_photo_list.clear()
          #      photo_number = PHOTO_NUMBER_SENT
          #  
          #  else:
          #      pass

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

