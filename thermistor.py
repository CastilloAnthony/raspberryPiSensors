termistor_pin = 0

import RPi.GPIO as GPIO
import ADC0834
import time
import math

def init():
    ADC0834.setup()

def loop():
    while True:
        analogVal = ADC0834.getResult()
        Vr = 5 * float(analogVal) / 255
        if (5 - Vr) == 0:
            Rt = 10000 * Vr / 0.01
        else:
            Rt = 10000 * Vr / (5 - Vr)
        print('Analog Val: %.2f Voltage: %.2f V Resitance: %.2f Ohms' % (analogVal, Vr, Rt))
        temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15+25)))
        Cel = temp - 273.15
        Fah = Cel * 1.8 + 32
        print ('Celsius: %.2f °C  Fahrenheit: %.2f ℉' % (Cel, Fah))
        
        time.sleep(0.2)

if __name__ == '__main__':
    init()
    try:
        loop()
    except KeyboardInterrupt:
        ADC0834.destroy()

# cmd=0x40
# therm_value = bus.read_byte_data(self.__thermistor_pin, cmd+0)
# voltage = therm_value / 255.0 * 3.3
# # Rt = 10 * voltage / (3.3 - voltage)
# Rt = (voltage*10000)/(3.3-voltage) # Rt = (V_out*R_initial)/(V_in-V_out)
# tempK = 1/(1/(273.15 + 25) + math.log(Rt/10)/3950.0)
# tempC = tempK - 273.15
# print('ADC Value : %d, Voltage : %.2f, Temperature: %.2f'.format(therm_value, voltage, tempC))