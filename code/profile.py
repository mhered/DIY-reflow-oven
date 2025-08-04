"""
Temperature Profile Management for Reflow Oven
Handles temperature profiles with multiple phases
"""

import json
import time


class TemperaturePhase:
    """Represents a single phase in a temperature profile"""
    
    def __init__(self, name, start_temp, end_temp, 
                 duration_minutes=None, 
                 climb_rate_per_minute=None):
        self.name = name
        self.start_temp = start_temp
        self.end_temp = end_temp
        
        # Either duration OR climb rate must be specified
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes
            self.climb_rate_per_minute = (end_temp - start_temp) / duration_minutes if duration_minutes > 0 else 0
            self.type = "time_based"
        elif climb_rate_per_minute is not None:
            self.climb_rate_per_minute = climb_rate_per_minute
            self.duration_minutes = abs(end_temp - start_temp) / abs(climb_rate_per_minute) if climb_rate_per_minute != 0 else 0
            self.type = "rate_based"
        else:
            raise ValueError("Either duration_minutes or climb_rate_per_minute must be specified")
    
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
            'duration_minutes': self.duration_minutes,
            'climb_rate_per_minute': self.climb_rate_per_minute,
            'type': self.type
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create phase from dictionary"""
        return cls(
            name=data['name'],
            start_temp=data['start_temp'],
            end_temp=data['end_temp'],
            duration_minutes=data.get('duration_minutes'),
            climb_rate_per_minute=data.get('climb_rate_per_minute')
        )


class TemperatureProfile:
    """Represents a complete temperature profile with multiple phases"""
    
    def __init__(self, name, phases):
        self.name = name
        self.phases = phases
        self.total_duration = sum(phase.duration_minutes for phase in phases)
        self.validate()
    
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
        return {
            'name': self.name,
            'total_duration': self.total_duration,
            'phases': [phase.to_dict() for phase in self.phases]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create profile from dictionary"""
        phases = [TemperaturePhase.from_dict(phase_data) for phase_data in data['phases']]
        return cls(name=data['name'], phases=phases)
    
    def save_to_file(self, filepath):
        """Save profile to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath):
        """Load profile from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


# Example profiles for testing
def create_example_profiles():
    """Create some example reflow profiles"""
    
    # Lead-free reflow profile
    lead_free_phases = [
        TemperaturePhase("Preheat", 25, 150, duration_minutes=4),
        TemperaturePhase("Soak", 150, 180, duration_minutes=2),
        TemperaturePhase("Reflow", 180, 245, duration_minutes=1.5),
        TemperaturePhase("Peak", 245, 245, duration_minutes=0.5),
        TemperaturePhase("Cooling", 245, 100, climb_rate_per_minute=-60),
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
