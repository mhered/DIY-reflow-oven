import random
import time

from display import Display
from server import WebServer
from thermistor import Thermistor
from heater import Heater
from wifi import connect


# initialize sensor
SENSOR_PIN = None # 26 to use a physical sensor, None to simulate temp readings
sensor = Thermistor(pin = SENSOR_PIN)

# initialize heater controller
HEATER_PIN = 22
heater = Heater(pin = HEATER_PIN)

# Connect to Wi-Fi
ip_address = connect()

# initialize Display
display = Display()

# Confirm it's working
display.show_message("Online at:", ip_address)

# Start web server
server = WebServer()

time.sleep(5)


INITIAL_TEMP = 25 	# C
NOISE = 0.1 		# C
HEATING = 0.4 		# C/sec
COOLING = -0.3 		# C/sec
last_temperature = INITIAL_TEMP
WAIT = 1 			# sec

# Main loop
while True:
    if sensor.pin is None:
        # If no sensor, simulate temperature with random noise and heating / cooling
        temperature = last_temperature + NOISE * (random.random() - 0.5) * 2
        if heater.is_on:
            temperature += HEATING
        else:
            temperature += COOLING 
    else:
        temperature = sensor.read_temp()
    last_temperature = temperature

     # Use heater class to control heating logic
    heater_on = heater.set_state(temperature, server.target_temp)

    display.show_temp("Temperature", temperature, heater_on)

    server.serve_temperature_once(temperature)
    server.serve_heater_state_once(heater_on)

    print("Temp:", temperature)

    time.sleep(WAIT)