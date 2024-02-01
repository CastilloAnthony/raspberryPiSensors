import RPi.GPIO as GPIO
import adafruit_dht as DHT
import board
from rpi_lcd import LCD
from signal import signal, SIGTERM, SIGHUP, pause
from threading import Thread
import time
from pathlib import Path
import logging
import math
import ADC0834

class Arbiter():
	def __init__(self):
		self.__currTime = time.localtime()
		logging.basicConfig(filename='runtime_'+self.configureFilename(self.__currTime)+'.log', encoding='utf-8', level=logging.DEBUG)
		logging.info(time.ctime()+' - Initializing...')
		logging.info(time.ctime()+' - Saving log to runtime_'+self.configureFilename(self.__currTime)+'.log')
		# self.__led_pin=13 # BOARD
		self.__led_pin=21 # BCM
		self._led = False
		# self.__dht_pin=16 # BOARD
		self.__dht_pin=23
		self.__lcd = LCD()
		self.__temperature_c = 0
		self.__temperature_f = 0
		self.__humidity = 0
		self.__running = True
		ADC0834.setup()
		
		self.__threads = []
		signal(SIGTERM, self.safe_exit)
		signal(SIGHUP, self.safe_exit)
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
		del self.__led_pin, self.__dht_pin, self.__lcd, self.__temperature_c, self.__temperature_f, self.__humidity, self.__running, self.__filename
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
		self.__threads.append(Thread(target=self.led_control, name='led_control'))
		self.__threads[len(self.__threads)-1].start()
		self.__threads.append(Thread(target=self.temperature, name='temperature'))
		self.__threads[len(self.__threads)-1].start()
		self.__threads.append(Thread(target=self.lcd, name='lcd'))
		self.__threads[len(self.__threads)-1].start()
		exit_list = ['quit', 'exit', 'q']
		temperature = ['temp', 'temperature', 'tp', 't',]# 'humd', 'humidity', 'hd', 'h']
		while self.__running:
			user_input = input('Command: ')
			if user_input.lower() in exit_list:
				print(time.ctime()+' - Exiting...')
				logging.info(time.ctime()+' - Exiting...')
				self.__running = False
			elif user_input.lower() in temperature:
				print(time.ctime()+' - Temperature:{0:0.1f}C /{1:0.1f}F'.format(self.__temperature_c, self.__temperature_f))#, self.__humidity))
			elif user_input.lower() == 'threads':
				for i in self.__threads:
					print(time.ctime()+' - '+str(i.name)+' Alive Status:'+str(i.is_alive()))
			elif user_input.lower() == 'restart':
				print(time.ctime()+' - Restarting threads...')
				while len(self.__threads) > 0:
					print(time.ctime()+' - Killing thread '+str(self.__threads[0].name))
					self.__threads[0].join(1)
					if self.__threads[0].is_alive():
						self.__threads[0].terminate()
					del self.__threads[0]
				self.__threads.append(Thread(target=self.led_control, name='led_control'))
				self.__threads[len(self.__threads)-1].start()
				self.__threads.append(Thread(target=self.temperature, name='temperature'))
				self.__threads[len(self.__threads)-1].start()
				self.__threads.append(Thread(target=self.lcd, name='lcd'))
				self.__threads[len(self.__threads)-1].start()
			elif user_input.lower() == 'help':
				print('Currently supported commands are:\n')
				[print(i) for i in exit_list]
				[print(j) for j in temperature]
				print('threads')
				print('restart')
			else:
				print('Command not recognized.')
		self.__running = False
		self.__threads[len(self.__threads)-2].join()
		self.__threads[len(self.__threads)-1].join()
		# self.clear()

	def lcd(self):
		motion = False
		currTimestamp = time.time()
		while self.__running:
			currTime = time.localtime()
			if (time.time() - currTimestamp) >= 1:
				currTimeString = ''
				if len(str(currTime[3])) == 1:
					currTimeString += '0'+str(currTime[3])
				else:
					currTimeString += str(currTime[3])
				if len(str(currTime[4])) == 1:
					currTimeString += '0'+str(currTime[4])
				else:
					currTimeString += str(currTime[4])
				if len(str(currTime[5])) == 1:
					currTimeString += '0'+str(currTime[5])
				else:
					currTimeString += str(currTime[5])
				self.__lcd.text('Time: '+str(currTimeString[:2])+':'+str(currTimeString[2:4])+':'+str(currTimeString[4:]), 1)
				self.__lcd.text("T:{0:0.1f}C / {1:0.1f}F".format(self.__temperature_c, self.__temperature_f), 2)#, self.__humidity), 2)
				del currTime, currTimeString
				# time.sleep(0.25)

	def temperature(self):
		# GPIO.setup(self.__led_pin, GPIO.OUT)
		# GPIO.output(self.__led_pin,False)
		temperature_list = []
		# sampleSize = 10
		while self.__running:
			try:
				# Getting Thermistor readings
				analogVal = ADC0834.getResult()
				Vr = 5 * float(analogVal) / 255
				Rt = 10000 * Vr / (5 - Vr)
				temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15+25)))
				Cel = temp - 273.15
				# Fah = Cel * 1.8 + 32
				# self.__temperature_c = Cel
				# self.__temperature_f = Fah
				temperature_list.append(Cel)
				# if len(temperature_list) >= sampleSize:
				if round(time.time()) % 5 == 0:
					# GPIO.output(self.__led_pin,True)
					self.__led = True
					temperature_c = 0
					for i in temperature_list:
						temperature_c += i
					self.__temperature_c = temperature_c / len(temperature_list)
					self.__temperature_f = self.__temperature_c * 1.8 +32
					currTime = time.localtime()
					if currTime[2] == self.__currTime[2]: # Use the current file
						with open(self.__filename, 'a', encoding='utf-8') as file:
							file.write(str(time.time())+','+str(self.__humidity)+','+str(self.__temperature_c))
					else: # Create a new file
						self.__currTime = currTime
						self.__filename = './data/sensor_data_'+self.configureFilename(self.__currTime)+'.csv'
						with open(self.__filename, 'w', encoding='utf-8') as file:
							file.write('time_seconds,humidity,temperature')
							file.write(str(time.time())+','+str(self.__humidity)+','+str(self.__temperature_c))
						logging.info(time.ctime()+' - created '+self.__filename+' in the ./data folder.')
					del currTime
					del temperature_list
					temperature_list = []
					# time.sleep(1)
					# GPIO.output(self.__led_pin,False)
				# else:
					# time.sleep(4/sampleSize)
			except Exception as error:
				logging.error(time.ctime()+' - '+str(error))

	def led_control(self):
		GPIO.setup(self.__led_pin, GPIO.OUT)
		GPIO.output(self.__led_pin,False)
		while self.__running:
			if self.__led:
				GPIO.output(self.__led_pin,True)
				time.sleep(1)
				GPIO.output(self.__led_pin,False)
			time.sleep(0.1)

	def temp_hum(self):
		DHT_SENSOR=DHT.DHT11(board.D23)
		GPIO.setup(self.__led_pin, GPIO.OUT)
		GPIO.output(self.__led_pin,False)
		while self.__running:
			try:
				# Getting Thermistor readings
				analogVal = ADC0834.getResult()
				Vr = 5 * float(analogVal) / 255
				Rt = 10000 * Vr / (5 - Vr)
				temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15+25)))
				Cel = temp - 273.15
				Fah = Cel * 1.8 + 32
				self.__temperature_c = Cel
				self.__temperature_f = Fah

				# Print the values to the serial port
				temperature_c = DHT_SENSOR.temperature
				temperature_f = temperature_c * (9 / 5) + 32
				humidity = DHT_SENSOR.humidity
					
				# print(
				# 	"Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
				# 		temperature_f, temperature_c, humidity
				# 	)
				# )
				if temperature_c != None and humidity != None:
					GPIO.output(self.__led_pin,True)
					# print ('Celsius: %.2f °C  Fahrenheit: %.2f ℉' % (Cel, Fah))
					# if not temperature_c+1 >= Cel and not temperature_c-1 <= Cel:
					# 	self.__humidity, self.__temperature_c = humidity, Cel
					# else:
					# 	# Adding the two temperature readings together and dividing by two, finding their average
					# self.__humidity, self.__temperature_c = humidity, temperature_c
					self.__humidity = humidity
					currTime = time.localtime()
					if currTime[2] == self.__currTime[2]: # Use the current file
						with open(self.__filename, 'a', encoding='utf-8') as file:
							file.write(str(time.time())+','+str(self.__humidity)+','+str(self.__temperature_c))
					else: # Create a new file
						self.__currTime = currTime
						self.__filename = './data/sensor_data_'+self.configureFilename(self.__currTime)+'.csv'
						with open(self.__filename, 'w', encoding='utf-8') as file:
							file.write('time_seconds,humidity,temperature')
							file.write(str(time.time())+','+str(self.__humidity)+','+str(self.__temperature_c))
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
			time.sleep(1.0)
			GPIO.output(self.__led_pin,False)
			time.sleep(1.0)
# end Arbiter

if __name__ == "__main__":
	print(time.ctime())
	newArbiter = Arbiter()
	newArbiter.start()
