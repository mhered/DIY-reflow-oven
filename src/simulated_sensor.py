import random

class SimulatedSensor:
    """
    Simulates temperature readings.

    Parameters:
     - ambient_temp (float): Ambient temperature in Celsius.
     - noise (float): Random noise in C to add to the temperature reading.
     - heating (float): Rate of temperature increase when heater is on (C/sec).
     - cooling_k (float): Cooling constant for Newton's law of cooling.
    """

    def __init__(self, ambient_temp = 25, noise = 0.1, heating = 0.5, cooling_k = 0.08):
        
        self.ambient_temp = ambient_temp
        self.noise = noise
        self.heating = heating
        self.cooling_k = cooling_k

        self.temperature = ambient_temp  # Start at ambient temperature

    def __repr__(self):
        return "<SimulatedSensor ambient_temp={} noise={} heating={} cooling_k={}>".format(
            self.ambient_temp, self.noise, self.heating, self.cooling_k
        )

    def simu_temp(self, heater_on):
        # Simulate reading the temperature
        self.temperature += self.noise * (random.random() - 0.5) * 2
        if heater_on:
            # If the heater is on, increase the temperature
            self.temperature += self.heating
        else:
            self.temperature -= self.cooling_k * (self.temperature - self.ambient_temp)
        return self.temperature
