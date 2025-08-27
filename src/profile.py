import json

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
        try:
            return cls(
                name=data['name'],
                start_temp=data['start_temp'],
                end_temp=data['end_temp'],
                duration_minutes=data['duration_minutes']
            )
        except KeyError as e:
            debug_print("Missing required field: {}".format(e))
            raise
        except Exception as e:
            debug_print("Error creating phase: {}".format(e))
            raise


class TemperatureProfile:
    """Represents a complete temperature profile with multiple phases"""
    
    def __init__(self, name, phases):
        # Store original long name
        self.display_name = name
        # Create shorter name for UI and URLs
        self.name = self._make_short_name(name)
        self.phases = phases
        self.total_duration = sum(phase.duration_minutes for phase in phases)
        self.validate()
    
    def _make_short_name(self, name):
        """Generate a shorter name by clipping to 20 characters if needed"""
        return name[:20] if len(name) > 20 else name
    
    def validate(self):
        """Validate profile consistency"""
        if not self.phases:
            raise ValueError("Profile must have at least one phase")
        
        # Check phase continuity (end temp of phase N should match start temp of phase N+1)
        for i in range(len(self.phases) - 1):
            current_end = self.phases[i].end_temp
            next_start = self.phases[i + 1].start_temp
            if abs(current_end - next_start) > 0.1:  # 0.1°C tolerance
                print("Warning: Phase '{}' ends at {}°C but next phase '{}' starts at {}°C".format(
                    self.phases[i].name, current_end, self.phases[i+1].name, next_start))
    
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
        try:
            phases_list = [phase.to_dict() for phase in self.phases]
            return {
                'name': self.display_name,  # Store full name in JSON
                'phases': phases_list
            }
        except Exception as e:
            print("Error converting profile to dict: {}".format(e))
            raise
    
    @classmethod
    def from_dict(cls, data):
        """Create profile from dictionary"""
        try:
            phases = []
            for phase_data in data.get('phases', []):
                phase = TemperaturePhase.from_dict(phase_data)
                phases.append(phase)
            
            result = cls(data['name'], phases)
            # Show a summary of the phases
            debug_print("Loaded profile: {} ({} phases)".format(data['name'], len(phases)))
            for i, phase in enumerate(phases):
                debug_print("  Phase {}: {} ({} -> {}°C, {}min)".format(
                    i+1, phase.name, phase.start_temp, phase.end_temp, phase.duration_minutes))
            return result
        except Exception as e:
            print("Error loading profile: {}".format(e))
            raise
    
    def save_to_file(self, directory):
        """Save profile to JSON file in specified directory"""
        try:
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
                
            debug_print("Saved profile: {} to {}".format(self.name, filename))
        except Exception as e:
            print("Error saving profile: {}".format(e))
            raise
    
    @classmethod
    def load_from_file(cls, filepath):
        """Load profile from JSON file - MicroPython compatible"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("File is empty")
                data = json.loads(content)
            debug_print("Loading profile: {} from {}".format(
                data.get('name', 'NO NAME'),
                filepath.split('/')[-1]))
            return cls.from_dict(data)
        except Exception as e:
            print("Error loading profile: {}".format(e))
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
