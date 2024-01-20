import RPi.GPIO as GPIO
import time

# led=7
led=13
GPIO.setmode(GPIO.BOARD)
GPIO.setup(led,GPIO.OUT)

GPIO.output(led,False)
for i in range(10):
	GPIO.output(led,True)
	time.sleep(1)
	GPIO.output(led,False)
	time.sleep(1)

GPIO.cleanup()
