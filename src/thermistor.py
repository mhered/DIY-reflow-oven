from machine import ADC
import math

class Thermistor:
    """
    Reads temperature from an NTC thermistor using a voltage divider.

    Parameters:
    - pin (int): ADC pin number (default: 26 for GPIO26 / ADC0)
    - vcc (float): Supply voltage in volts (default: 3.3V)
    - series_resistor (float): Resistance of the fixed resistor in ohms (default: 10000 Ohms)
    - beta (float): Thermistor beta coefficient (default: 3950)
    - r0 (float): Thermistor resistance at T0 in ohms (default: 10000 Ohms)
    - t0 (float): Reference temperature in Kelvin (default: 25°C > 298.15K)
    """

    def __init__(self, pin=None, vcc=3.3, series_resistor=10000, beta=3950, r0=10000, t0=25 + 273.15):
        self.pin = pin
        if self.pin:
            self.adc = ADC(pin)
        else:
            self.adc = None
        self.vcc = vcc
        self.series_resistor = series_resistor
        self.beta = beta
        self.r0 = r0
        self.t0 = t0  # in Kelvin

    def __repr__(self):
        if self.pin:
            return "<Sensor on pin {}>".format(self.adc)
        else: 
            return "No sensor"

    def read_temp(self):
        if self.pin:
            raw = self.adc.read_u16()  # 0–65535
            voltage = self.vcc * raw / 65535
            if voltage == 0 or voltage >= self.vcc:
                return None  # avoid division by 0
            rt = self.series_resistor * voltage / (self.vcc - voltage)
            tempK = 1 / (1/self.t0 + math.log(rt / self.r0) / self.beta)
            tempC = tempK - 273.15
            return tempC
        else:
            return None   

