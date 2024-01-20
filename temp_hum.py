import adafruit_dht
import board
#import RPi.GPIO as GPIO
import time

DHT_SENSOR=adafruit_dht.DHT11(board.D18)
# DHT_PIN=12
DHT_PIN=18

while True:
	humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
	if humidity is not None and temperature is not None:
		print("Temp={0:0.1f}C Humidity={1:0.1f}%".format(temperature, humidity))
	else:
		print("Sensor failure. Check wiring.");
	time.sleep(3)
