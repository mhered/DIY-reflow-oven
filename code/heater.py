"""
Heater control class for DIY reflow oven
Handles heater logic with support for simple on/off control
and extensible for future PID/hysteresis implementations
"""

class Heater:
    def __init__(self, pin=None, hysteresis=1.0):
        """
        Initialize heater controller
        
        Args:
            pin: GPIO pin for heater control (if using physical pin)
            hysteresis: Temperature difference for hysteresis control (°C)
        """
        self.pin = pin
        self.hysteresis = hysteresis
        self.is_on = False
        self.last_state = False
        
        # Initialize GPIO if pin is provided
        if self.pin:
            try:
                from machine import Pin
                self.heater_pin = Pin(self.pin, Pin.OUT)
                self.heater_pin.off()
            except ImportError:
                print("Warning: GPIO not available, heater will be simulated")
                self.heater_pin = None
        else:
            self.heater_pin = None
    
    def set_state(self, current_temp, target_temp):
        """
        Update heater state based on current and target temperatures
        Uses simple hysteresis control to prevent rapid on/off cycling
        
        Args:
            current_temp (float): Current temperature reading
            target_temp (float): Desired target temperature
            
        Returns:
            bool: True if heater should be on, False otherwise
        """
        # Simple hysteresis control
        if not self.is_on:
            # Turn on if temperature is below target minus hysteresis
            if current_temp < target_temp - self.hysteresis:
                self.is_on = True
        else:
            # Turn off if temperature reaches target (no overshoot allowed for safety)
            if current_temp >= target_temp:
                self.is_on = False
        
        # Apply the state to physical hardware
        self._set_physical_state(self.is_on)
        
        return self.is_on
    
    def _set_physical_state(self, state):
        """Set the physical heater state"""
        if self.heater_pin:
            if state:
                self.heater_pin.on()
            else:
                self.heater_pin.off()
        
        # Log state changes
        if state != self.last_state:
            print(f"Heater {'ON' if state else 'OFF'}")
            self.last_state = state
      
    def get_state(self):
        """Get current heater state"""
        return self.is_on
    
    def emergency_stop(self):
        """Emergency stop - immediately turn off heater"""
        self.is_on = False
        self._set_physical_state(False)
        print("EMERGENCY STOP: Heater turned off")
    
    def set_hysteresis(self, hysteresis):
        """
        Set hysteresis value for temperature control
        
        Args:
            hysteresis (float): Temperature difference in °C
        """
        self.hysteresis = max(0.1, hysteresis)  # Minimum 0.1°C hysteresis
        print(f"Hysteresis set to {self.hysteresis}°C")
