# Developed by Anthony Castillo
# Most of code retrived from
# https://github.com/pimylifeup/motion_sensor/blob/master/motion_sensor.py

import RPi.GPIO as GPIO
import time

pir_sensor=11
led=6

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pir_sensor, GPIO.IN)
GPIO.setup(led, GPIO.OUT)

current_state=0
GPIO.output(led,False)
try:
	while True:
		time.sleep(0.1)
		current_state=GPIO.input(pir_sensor)
		if current_state == 1:
			GPIO.output(led,True)
			print("GPIO pin %s is %s" % (pir_sensor, current_state))
			time.sleep(5)
			GPIO.output(led,False)
except KeyboardInterrupt:
	pass
finally:
	GPIO.cleanup()
