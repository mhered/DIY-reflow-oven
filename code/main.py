import random
import time

from display import Display
from server import WebServer
from thermistor import Thermistor
from heater import Heater
from wifi import connect

# initialize temperature sensor
SENSOR_PIN = None # 26 to use a physical sensor, None to simulate temp readings
sensor = Thermistor(pin = SENSOR_PIN)

# initialize heater controller
HEATER_PIN = 22 # 22 to use a physical heater, None to simulate
HYSTERESIS = 1.0
MIN_TARGET_TEMP = 0.0
MAX_TARGET_TEMP = 300.0
INITIAL_TARGET_TEMP = None  # Start with no target (heater off)

heater = Heater(pin=HEATER_PIN,
                hysteresis=HYSTERESIS,
                min_temp=MIN_TARGET_TEMP,
                max_temp=MAX_TARGET_TEMP,
                target_temp=INITIAL_TARGET_TEMP)

# Connect to Wi-Fi
ip_address = connect()

# initialize Display
display = Display()

# Confirm it's working
display.show_message("Online at:", ip_address)

# Start web server
server = WebServer(heater)

time.sleep(5)

# Temperature Simulation parameters
AMBIENT_TEMP = 25 	# C
NOISE = 0.1 		# C
HEATING = 0.4 		# C/sec
COOLING_K = 0.08 		# Newton's cooling constant

temperature = AMBIENT_TEMP  # Start at ambient temperature

# Time to wait between temperature updates
WAIT = 1 			# sec

# Main loop
while True:
    if sensor.pin is None:
        # If no sensor, simulate temperature with random noise and heating / cooling
        temperature += NOISE * (random.random() - 0.5) * 2
        if heater.is_on:
            temperature += HEATING
        else:
            temperature -= COOLING_K * (temperature - AMBIENT_TEMP)
    else:
        temperature = sensor.read_temp()

    # Use heater class to control heating logic - heater now manages its own target
    # Check if profile manager has an active profile and update target accordingly
    profile_target = server.update_profiles()
    if profile_target is not None:
        # Profile is active, use profile target
        heater.set_target_temp(profile_target)
    else:
        # No profile active, heater stays off
        heater.set_target_temp(None)

    heater_on = heater.set_state(temperature)

    # Update current temperature and heater state
    
    # in OLED display
    display.show_temp("Temperature", temperature, heater_on)
    
    # in web server
    server.serve_temperature_once(temperature)
    server.serve_heater_state_once(heater_on)

    # in stdout
    print("Temp:", temperature)

    time.sleep(WAIT)