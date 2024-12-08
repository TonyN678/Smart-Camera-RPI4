# Set up libraries and overall settings
import RPi.GPIO as GPIO  # Imports the standard Raspberry Pi GPIO library
from time import sleep   # Imports sleep (aka wait or pause) into the program

# GPIO.BOARD - for taking pin value as white column (j8 Pin)
# GPIO.BCM - for taking pin value as the number after the letter GPIO eg. GPIO17, control pin = 17
GPIO.setmode(GPIO.BOARD) # Sets the pin numbering system to use the physical layout

# Set up pin 8 for PWM (TIlT)
GPIO.setup(8,GPIO.OUT) 
tilt = GPIO.PWM(8, 50)  
tilt.start(0)           

# Set up pin 16 for PWM (PAN)
GPIO.setup(16,GPIO.OUT)
pan = GPIO.PWM(16, 50) 
pan.start(0)           

# Move the servo back and forth
while True:
    tilt.ChangeDutyCycle(6)     # Changes the pulse width to 3 (so moves the servo)
    sleep(1)                 # Wait 1 second
    tilt.ChangeDutyCycle(12)    # Changes the pulse width to 12 (so moves the servo)
    sleep(1)

    pan.ChangeDutyCycle(7)     # Changes the pulse width to 3 (so moves the servo)
    sleep(1)                 # Wait 1 second
    pan.ChangeDutyCycle(12)    # Changes the pulse width to 12 (so moves the servo)
    sleep(1)
# Clean up everything
pan.stop()                 # At the end of the program, stop the PWM
tilt.stop()                 # At the end of the program, stop the PWM
GPIO.cleanup()           # Resets the GPIO pins back to defaults
