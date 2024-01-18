import RPi.GPIO as GPIO
import Adafruit_DHT as DHT
from rpi_lcd import LCD
from signal import signal, SIGTERM, SIGHUP, pause
from threading import Thread
import time

class Arbiter():
	def __init__(self):
		self.__led_pin=7
		self.__pir_pin=11
		self.__dht_pin=12
		self.__lcd = None
		#self.__lcd = LCD()
		self.__temperature = 0
		self.__humidity = 0
		self.__running = True
		self.__DHT_SENSOR=DHT.DHT11
		self.__currTime = time.localtime()
		self.__filename = './logs/sensor_data_'+str(time.localtime()[3])+str(time.localtime()[4])+str(time.localtime()[5])+'.csv'
		with open(self.__filename, 'w', encoding="utf-8") as file:
			file.write('time,humidity,temperature')
		del self.__currTime
		self.__threads = []
		signal(SIGTERM, self.safe_exit)
		signal(SIGHUP, self.safe_exit)
		
	def __del__(self):
		self.clear()
		del self.__led_pin, self.__pir_pin, self.__dht_pin, self.__DHT_SENSOR, self.__lcd, self.__temperature, self.__humidity, self.__running, self.__filename
		while len(self.__threads) > 0:
			if self.__threads[-1].is_alive():
				self.__threads[-1].join(1)
				if self.__threads[-1].is_alive():
					self.__threads[-1].terminate()
			del self.__threads[-1]
		del self.__threads

	def clear(self):
		GPIO.cleanup()
		#self.__lcd.clear()

	def safe_exit(signum, frame):
		exit(1)

	def start(self):
		self.__threads.append(Thread(target=self.temp_hum, name='temp_hum'))
		self.__threads[len(self.__threads)-1].start()
		self.__threads.append(Thread(target=self.lcd, name='lcd'))
		self.__threads[len(self.__threads)-1].start()
		exit_list = ['quit', 'exit', 'q']
		while self.__running:
			user_input = input('Command: ')
			if user_input.lower() in exit_list:
				self.__running = False
		self.__running = False
		self.__threads[len(self.__threads)-2].join()
		self.__threads[len(self.__threads)-1].join()
		#self.clear()

	def lcd(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setup(self.__led_pin, GPIO.OUT)
		GPIO.setup(self.__pir_pin, GPIO.IN)
		GPIO.output(self.__led_pin,False)
		motion = False
		while self.__running:
			motion = GPIO.input(self.__pir_pin)
			if motion:
				GPIO.output(self.__led_pin,True)
				self.__lcd.text(str(time.localtime()[3])+':'+str(time.localtime()[4])+':'+str(time.localtime()[5]), 1)
				self.__lcd.text("Tp:{0:0.1f}C Hd:{1:0.1f}%".format(self.__temperature, self.__humidity), 2)
				time.sleep(0.25)
			else:
				GPIO.output(self.__led_pin,False)
		GPIO.output(self.__led_pin,False)
		self.clear()

	def temp_hum(self):
		while self.__running:
			humidity, temperature = DHT.read(self.__DHT_SENSOR, self.__dht_pin)
			if humidity is not None and temperature is not None:
				self.__humidity, self.__temperature = humidity, temperature
				with open(self.__filename, 'a', encoding="utf-8") as file:
					file.write(str(time.time())+','+str(self.__humidity)+','+str(self.__temperature))
			else:
				print("Could not read data from humidity sensor.")
			time.sleep(1)
# end Arbiter

if __name__ == "__main__":
	print(str(time.localtime()[3])+':'+str(time.localtime()[4])+':'+str(time.localtime()[5]))
	newArbiter = Arbiter()
	newArbiter.start()
