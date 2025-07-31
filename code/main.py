from display import Display
from server import WebServer
from thermistor import Thermistor

import time
from wifi import connect


# initialize sensor
sensor = Thermistor()

# Connect to Wi-Fi
ip_address = connect()

# initialize Display
display = Display()

# Confirm it's working
display.show_message("Online at:", ip_address)

# Start web server
server = WebServer()

time.sleep(5)



# Main loop
while True:
    temperature = sensor.read_temp()
    display.show_temp("Temperature", temperature, "C")
    server.serve_once(temperature)
    print("Temp:", temperature)
    time.sleep(1)