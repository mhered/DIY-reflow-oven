"""
Temperature Profile Management for Reflow Oven
Handles temperature profiles with multiple phases
"""

import json
import time

# Global debug flag - can be set from main.py
DEBUG_PROFILES = False

def set_profile_debug(enabled):
    """Set global debug flag for profile operations"""
    global DEBUG_PROFILES
    DEBUG_PROFILES = enabled

def debug_print(message):
    """Print debug message only if debug is enabled"""
    if DEBUG_PROFILES:
        print("DEBUG: {}".format(message))

class TemperaturePhase:
    """Represents a single phase in a temperature profile"""
    
    def __init__(self, name, start_temp, end_temp, duration_minutes):
        self.name = name
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.duration_minutes = duration_minutes
    
    def get_target_temp(self, elapsed_minutes):
        """Calculate target temperature for given elapsed time in this phase"""
        if elapsed_minutes <= 0:
            return self.start_temp
        elif elapsed_minutes >= self.duration_minutes:
            return self.end_temp
        else:
            # Linear interpolation
            progress = elapsed_minutes / self.duration_minutes
            return self.start_temp + (self.end_temp - self.start_temp) * progress
    
    def to_dict(self):
        """Convert phase to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'start_temp': self.start_temp,
            'end_temp': self.end_temp,
            'duration_minutes': self.duration_minutes
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create phase from dictionary"""
        return cls(
            name=data['name'],
            start_temp=data['start_temp'],
            end_temp=data['end_temp'],
            duration_minutes=data['duration_minutes']
        )


class TemperatureProfile:
    """Represents a complete temperature profile with multiple phases"""
    
    def __init__(self, name, phases):
        debug_print("Starting TemperatureProfile.__init__ for '{}'".format(name))
        self.name = name
        self.phases = phases
        self.total_duration = sum(phase.duration_minutes for phase in phases)
        self.validate()
        debug_print("TemperatureProfile.__init__ completed for '{}'".format(name))
    
    def validate(self):
        """Validate profile consistency"""
        debug_print("Validating profile consistency")
        if not self.phases:
            raise ValueError("Profile must have at least one phase")
        
        # Check phase continuity (end temp of phase N should match start temp of phase N+1)
        for i in range(len(self.phases) - 1):
            current_end = self.phases[i].end_temp
            next_start = self.phases[i + 1].start_temp
            if abs(current_end - next_start) > 0.1:  # 0.1°C tolerance
                print("Warning: Phase '{}' ends at {}°C but next phase '{}' starts at {}°C".format(
                    self.phases[i].name, current_end, self.phases[i+1].name, next_start))
        debug_print("Profile validation completed")
    
    def get_current_phase_and_target(self, elapsed_minutes):
        """
        Get current phase index, name, and target temperature for given elapsed time
        Returns: (phase_index, phase_name, target_temperature)
        """
        if elapsed_minutes < 0:
            return 0, self.phases[0].name, self.phases[0].start_temp
        
        cumulative_time = 0
        for i, phase in enumerate(self.phases):
            if elapsed_minutes <= cumulative_time + phase.duration_minutes:
                phase_elapsed = elapsed_minutes - cumulative_time
                target_temp = phase.get_target_temp(phase_elapsed)
                return i, phase.name, target_temp
            cumulative_time += phase.duration_minutes
        
        # Profile completed
        last_phase = self.phases[-1]
        return len(self.phases) - 1, last_phase.name, last_phase.end_temp
    
    def is_complete(self, elapsed_minutes):
        """Check if profile execution is complete"""
        return elapsed_minutes >= self.total_duration
    
    def to_dict(self):
        """Convert profile to dictionary for JSON serialization"""
        debug_print("Converting profile '{}' to dictionary".format(self.name))
        try:
            phases_list = []
            for i, phase in enumerate(self.phases):
                debug_print("Converting phase {}: {}".format(i, phase.name))
                phase_dict = phase.to_dict()
                phases_list.append(phase_dict)
            
            result = {
                'name': self.name,
                'phases': phases_list
            }
            debug_print("Profile '{}' converted to dict successfully".format(self.name))
            return result
        except Exception as e:
            print("Error in to_dict for profile '{}': {}".format(self.name, e))
            raise
    
    @classmethod
    def from_dict(cls, data):
        """Create profile from dictionary"""
        debug_print("Creating profile from dict: {}".format(data['name']))
        phases = []
        for i, phase_data in enumerate(data['phases']):
            debug_print("Creating phase {}: {}".format(i, phase_data['name']))
            phase = TemperaturePhase.from_dict(phase_data)
            phases.append(phase)
        debug_print("Created {} phases for profile '{}'".format(len(phases), data['name']))
        
        # Bypass __init__ completely and manually set attributes to avoid MicroPython recursion bug
        try:
            # Create instance manually without calling __init__
            result = object.__new__(cls)
            debug_print("Created object instance for profile '{}'".format(data['name']))
            
            # Manually set all attributes that __init__ would set
            result.name = data['name']
            result.phases = phases
            result.total_duration = sum(phase.duration_minutes for phase in phases)
            
            # Manually validate (inline the validation logic)
            if not result.phases:
                raise ValueError("Profile must have at least one phase")
            
            # Check phase continuity manually
            for i in range(len(result.phases) - 1):
                current_end = result.phases[i].end_temp
                next_start = result.phases[i + 1].start_temp
                if abs(current_end - next_start) > 0.1:  # 0.1°C tolerance
                    print("Warning: Phase '{}' ends at {}°C but next phase '{}' starts at {}°C".format(
                        result.phases[i].name, current_end, result.phases[i+1].name, next_start))
            
            debug_print("Profile '{}' created successfully from dict".format(data['name']))
            return result
        except Exception as e:
            print("Error creating profile '{}' from dict: {}".format(data['name'], e))
            raise
    
    def save_to_file(self, directory):
        """Save profile to JSON file in specified directory"""
        try:
            debug_print("Saving profile '{}' to directory '{}'".format(self.name, directory))
            # Create filename from profile name
            filename = self.name.replace(' ', '_').replace('/', '_') + '.json'
            filepath = directory + '/' + filename
            
            profile_dict = self.to_dict()
            json_str = json.dumps(profile_dict)
            
            with open(filepath, 'w') as f:
                f.write(json_str)
            
            # Force file system sync on MicroPython to ensure file is written
            try:
                import os
                if hasattr(os, 'sync'):
                    os.sync()
            except Exception:
                pass  # Ignore if sync is not available
                
            debug_print("Profile '{}' saved successfully to '{}'".format(self.name, filepath))
        except Exception as e:
            print("Error saving profile '{}': {}".format(self.name, e))
            raise
    
    @classmethod
    def load_from_file(cls, filepath):
        """Load profile from JSON file - MicroPython compatible"""
        try:
            debug_print("Loading profile from file: {}".format(filepath))
            with open(filepath, 'r') as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("File is empty")
                data = json.loads(content)
            debug_print("Loaded profile '{}' from file".format(data['name']))
            result = cls.from_dict(data)
            debug_print("Profile '{}' loaded successfully".format(data['name']))
            return result
        except Exception as e:
            print("Error loading profile from {}: {}".format(filepath, e))
            raise


# Example profiles for testing
def create_example_profiles():
    """Create some example reflow profiles"""
    
    # Lead-free reflow profile
    lead_free_phases = [
        TemperaturePhase("Preheat", 25, 150, duration_minutes=4),
        TemperaturePhase("Soak", 150, 180, duration_minutes=2),
        TemperaturePhase("Reflow", 180, 245, duration_minutes=1.5),
        TemperaturePhase("Peak", 245, 245, duration_minutes=0.5),
        TemperaturePhase("Cooling", 245, 100, duration_minutes=2.4),  # ~60°C/min cooling
    ]
    
    # Simple test profile
    test_phases = [
        TemperaturePhase("Warm up", 25, 50, duration_minutes=2),
        TemperaturePhase("Hold", 50, 50, duration_minutes=1),
        TemperaturePhase("Cool down", 50, 25, duration_minutes=2),
    ]
    
    return [
        TemperatureProfile("Lead-free Reflow", lead_free_phases),
        TemperatureProfile("Test Profile", test_phases)
    ]
