import RPi.GPIO as GPIO
import adafruit_dht as DHT
import board
from rpi_lcd import LCD
from signal import signal, SIGTERM, SIGHUP, pause
from threading import Thread
import time
from pathlib import Path
import logging

class Arbiter():
	def __init__(self):
		self.__currTime = time.localtime()
		logging.basicConfig(filename='runtime_'+self.configureFilename(self.__currTime)+'.log', encoding='utf-8', level=logging.DEBUG)
		logging.info(time.ctime()+' - Initializing...')
		logging.info(time.ctime()+' - Saving log to runtime_'+self.configureFilename(self.__currTime)+'.log')
		self.__led_pin=13
		self.__pir_pin=15
		self.__dht_pin=16
		self.__lcd = LCD()
		self.__temperature = 0
		self.__humidity = 0
		self.__running = True
		
		self.__threads = []
		signal(SIGTERM, self.safe_exit)
		signal(SIGHUP, self.safe_exit)
		# self.__filename = './data/sensor_data_'+str(self.__currTime[0])+str(self.__currTime[1])+str(self.__currTime[2])+'.csv'
		self.__filename = './data/sensor_data_'+self.configureFilename(self.__currTime)+'.csv'
		if not Path('./data').is_dir():
			Path('./data').mkdir()
			logging.info(time.ctime()+' - ./data directory has been created.')
		if not Path('~'+self.__filename).is_file():
			with open(self.__filename, 'w', encoding='utf-8') as file:
				file.write('time_seconds,humidity,temperature')
			logging.info(time.ctime()+' - created '+self.__filename+' in the ./data folder.')
		logging.info(time.ctime()+' - Using ./data to store temperature and humidity data.')
		
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

	def configureFilename(self, timeData):
		currTimeString = str(timeData[0])
		if len(str(timeData[1])) == 1:
			currTimeString += '0'+str(timeData[1])
		else:
			currTimeString += str(timeData[1])
		if len(str(timeData[2])) == 1:
			currTimeString += '0'+str(timeData[2])
		else:
			currTimeString += str(timeData[2])
		return currTimeString
	
	def clear(self):
		GPIO.cleanup()
		self.__lcd.clear()

	def safe_exit(signum, frame):
		exit(1)

	def start(self):
		self.__threads.append(Thread(target=self.temp_hum, name='temp_hum'))
		self.__threads[len(self.__threads)-1].start()
		self.__threads.append(Thread(target=self.lcd, name='lcd'))
		self.__threads[len(self.__threads)-1].start()
		exit_list = ['quit', 'exit', 'q']
		temperature = ['temp', 'temperature', 'tp', 't', 'humd', 'humidity', 'hd', 'h']
		while self.__running:
			user_input = input('Command: ')
			if user_input.lower() in exit_list:
				print(time.ctime()+' - Exiting...')
				logging.info(time.ctime()+' - Exiting...')
				self.__running = False
			elif user_input.lower() in temperature:
				print(time.ctime()+' - Temperature:{0:0.1f}C Humidity:{1:0.1f}%'.format(self.__temperature, self.__humidity))
			elif user_input.lower() == 'help':
				print('Currently supported commands are:\n')
				[print(i) for i in exit_list]
				[print(j) for j in temperature]
			else:
				print('Command not recognized.')
		self.__running = False
		self.__threads[len(self.__threads)-2].join()
		self.__threads[len(self.__threads)-1].join()
		# self.clear()

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
				currTime = time.localtime()
				# self.__lcd.text(str(time.localtime()[3])+':'+str(time.localtime()[4])+':'+str(time.localtime()[5]), 1)
				self.__lcd.texT(str(currTime[3])+':'+str(currTime[4])+':'+str(currTime[5]), 1)
				self.__lcd.text("Tp:{0:0.1f}C Hd:{1:0.1f}%".format(self.__temperature, self.__humidity), 2)
				del currTime
				time.sleep(0.25)
			else:
				GPIO.output(self.__led_pin,False)
		GPIO.output(self.__led_pin,False)
		# self.clear()

	def temp_hum(self):
		DHT_SENSOR=DHT.DHT11(board.D23)
		while self.__running:
			try:
				# Print the values to the serial port
				temperature = DHT_SENSOR.temperature
				humidity = DHT_SENSOR.humidity
				print(
					"Temp: {:.1f} C    Humidity: {}% ".format(
						temperature, humidity
					)
				)
				if temperature != None and humidity != None:
					self.__humidity, self.__temperature = humidity, temperature
					currTime = time.localtime()
					if currTime[2] == self.__currTime[2]: # Use the current file
						with open(self.__filename, 'a', encoding='utf-8') as file:
							file.write(str(time.time())+','+str(self.__humidity)+','+str(self.__temperature))
					else: # Create a new file
						self.__currTime = currTime
						# self.__filename = './data/sensor_data_'+str(self.__currTime[0])+str(self.__currTime[1])+str(self.__currTime[2])+'.csv'
						self.__filename = './data/sensor_data_'+self.configureFilename(self.__currTime)+'.csv'
						with open(self.__filename, 'w', encoding='utf-8') as file:
							file.write('time_seconds,humidity,temperature')
							file.write(str(time.time())+','+str(self.__humidity)+','+str(self.__temperature))
						logging.info(time.ctime()+' - created '+self.__filename+' in the ./data folder.')
					del currTime
			except RuntimeError as error:
				# Errors happen fairly often, DHT's are hard to read, just keep going
				logging.error(time.ctime()+' - '+str(error.args[0]))
				time.sleep(2.0)
				continue
			except Exception as error:
				DHT_SENSOR.exit()
				logging.error(time.ctime()+' - '+str(error))
				raise error

			time.sleep(2.0)
# end Arbiter

if __name__ == "__main__":
	print(time.ctime())
	newArbiter = Arbiter()
	newArbiter.start()
