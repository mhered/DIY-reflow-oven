import random
import time

from display import Display
from server import WebServer

from thermistor import Thermistor
from simulated_sensor import SimulatedSensor
from max6675 import MAX6675
from machine import Pin

from heater import Heater
from wifi import connect
from profile import set_profile_debug

# Debug configuration - set to True to enable verbose profile logging
DEBUG_MODE = False  # Change to True for debug output
set_profile_debug(DEBUG_MODE)


# choose type of temperature sensor

class SensorType:
    THERMISTOR = 1
    MAX6675 = 2
    SIMULATED = 3

sensor_type = SensorType.MAX6675

# initialize temperature sensor

if sensor_type == SensorType.SIMULATED:
    simulated_sensor = SimulatedSensor()
elif sensor_type == SensorType.THERMISTOR:
    SENSOR_PIN = 26  # 26 to use a physical sensor
    thermistor_sensor = Thermistor(pin=SENSOR_PIN)
elif sensor_type == SensorType.MAX6675:
    sck = Pin(13, Pin.OUT) # orange cable
    cs = Pin(14, Pin.OUT) # yellow cable
    so = Pin(15, Pin.IN) # green cable
    max6675_sensor = MAX6675(sck, cs , so)

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

# Time to wait between temperature updates
WAIT = 0.5 			# sec

# Main loop
while True:
    if sensor_type == SensorType.SIMULATED:
        # Simulate temperature reading
        temperature = simulated_sensor.simu_temp(heater.is_on)
    elif sensor_type == SensorType.THERMISTOR:
        # Read temperature from thermistor
        temperature = thermistor_sensor.read_temp()
    elif sensor_type == SensorType.MAX6675:
        # Read temperature from MAX6675
        temperature = max6675_sensor.read()

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
    print("Temp: {:.2f} C".format(temperature))

    time.sleep(WAIT)