from machine import ADC#, Pin, I2C
# from ssd1306 import SSD1306_I2C
# import freesans20
# import writer
from display import Display

import time
import math
from wifi import connect

# Constants
VCC = 3.3                # Supply voltage
SERIES_RESISTOR = 10000  # 10kΩ fixed resistor
BETA = 3950.0            # Thermistor Beta coefficient
R0 = 10000.0             # Thermistor resistance at 25°C
T0 = 25 + 273.15         # Reference temp in Kelvin

# Thermistor connected to ADC0 (GPIO26)
adc = ADC(26)

# OLED Setup (SSD1306 128x64 I2C)
# i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
# oled = SSD1306_I2C(128, 64, i2c)

def read_temp():
    raw = adc.read_u16()  # 0–65535
    voltage = VCC * raw / 65535
    if voltage == 0 or voltage >= VCC:
        return None  # avoid division by 0
    Rt = SERIES_RESISTOR * voltage / (VCC - voltage)
    tempK = 1 / (1/T0 + math.log(Rt / R0) / BETA)
    tempC = tempK - 273.15
    return tempC

# def display_temp(title, value, units):
#     oled.fill(0)
#     if value is not None:
#         oled.text(title, 5, 5)
# 
#         font_writer = writer.Writer(oled,freesans20, verbose=False)
#         font_writer.set_textpos(5,30)
#         font_writer.printstring("{:.1f} {}".format(value, units))
#     else:
#         oled.text("NaN", 5, 5)
#         font_writer = writer.Writer(oled,freesans20)
#         font_writer.set_textpos(5,30)
#         font_writer.printstring("ERROR")
#     oled.show()
#     
# def show_message(title, text, line_height=16):
#     oled.fill(0)
#     oled.text(title, 5, 5)
#     lines = text.split("\n")
#     for i, line in enumerate(lines):
#         oled.text(line, 5, (i * line_height + 22))
#     oled.show()

# Connect to Wi-Fi
ip_address = connect()

# initialize Display
display = Display()

# Confirm it's working
display.show_message("Online at:", ip_address)
time.sleep(5)

# Main loop
while True:
    temperature = read_temp()
    display.show_temp("Temperature", temperature, "C")
    time.sleep(1)