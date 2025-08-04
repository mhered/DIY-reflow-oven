"""
Heater control class for DIY reflow oven
Handles heater logic with support for simple on/off control
and extensible for future PID/hysteresis implementations
"""

class Heater:
    def __init__(self, pin=None, 
                 hysteresis=1.0,
                 min_temp=0.0, 
                 max_temp=300.0,
                 target_temp=25.0):
        """
        Initialize heater controller
        
        Args:
            pin: GPIO pin for heater control (if using physical pin) - default None (simulated)
            hysteresis: Temperature difference for hysteresis control (°C) - default 1.0
            min_temp: Minimum temperature limit (°C) - default 0.0
            max_temp: Maximum temperature limit (°C) - default 300.0
            target_temp: Initial target temperature (°C) - default 25.0
        """
        self.pin = pin
        self.hysteresis = hysteresis   
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.target_temp = target_temp

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
    
    def set_state(self, current_temp, target_temp=None):
        """
        Update heater state based on current and target temperatures
        Uses simple hysteresis control to prevent rapid on/off cycling
        
        Args:
            current_temp (float): Current temperature reading
            target_temp (float): Optional override for target temperature.
                                If None, uses the heater's stored target_temp
            
        Returns:
            bool: True if heater should be on, False otherwise
        """
        # Use provided target or fall back to stored target
        if target_temp is None:
            target_temp = self.target_temp
        
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
            print("Heater {}".format('ON' if state else 'OFF'))
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
        print("Hysteresis set to {}°C".format(self.hysteresis))

    def set_target_temp(self, value):
        """Set target temperature with validation"""
        if self.min_temp <= value <= self.max_temp:
            self.target_temp = value
            print("Target temperature set to {}°C".format(self.target_temp))
            return {'status': 'ok', 'target': self.target_temp}
        else:
            return {'status': 'error', 'message': 'Target out of range ({}-{}°C)'.format(self.min_temp, self.max_temp)}, 400
    
    def get_target_temp(self):
        """Get current target temperature"""
        return self.target_temp
    
    def get_temp_limits(self):
        """Get temperature limits"""
        return {'min': self.min_temp, 'max': self.max_temp}
    
    def get_status(self):
        """Get complete heater status"""
        return {
            'target_temp': self.target_temp,
            'is_on': self.is_on,
            'hysteresis': self.hysteresis,
            'min_temp': self.min_temp,
            'max_temp': self.max_temp
        }
