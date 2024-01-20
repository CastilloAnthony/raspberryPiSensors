# Developed by Anthony Castillo
# Most of code retrived from
# https://github.com/pimylifeup/motion_sensor/blob/master/motion_sensor.py

import RPi.GPIO as GPIO
import time

# pir_sensor=11
pir_sensor=15
led=13

GPIO.setmode(GPIO.BOARD)
GPIO.setup(pir_sensor, GPIO.IN)
GPIO.setup(led, GPIO.OUT)

current_state=0
GPIO.output(led,False)

def lights():
	print(time.ctime()+'- Motion Detected!')
	GPIO.output(led,True)
	time.sleep(1)
	GPIO.output(led,False)

try:
	GPIO.add_event_detect(pir_sensor, GPIO.RISING, callback=lights)
	while True:
		# time.sleep(0.1)
		# current_state=GPIO.input(pir_sensor)
		# print("GPIO pin %s is %s" % (pir_sensor, current_state))
		time.sleep(1)
		# if current_state == 1:
		# 	GPIO.output(led,True)
		# 	# print("GPIO pin %s is %s" % (pir_sensor, current_state))
		# 	time.sleep(1)
		# else:
		# 	GPIO.output(led,False)
			
		
except KeyboardInterrupt:
	pass
finally:
	GPIO.cleanup()
