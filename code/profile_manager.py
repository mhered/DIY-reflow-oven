"""
Profile Manager for Temperature Control
Manages profile execution and integration with heater control
"""

import os
import time
from profile import TemperatureProfile, create_example_profiles


class ProfileManager:
    """Manages temperature profile execution and state"""
    
    def __init__(self, profiles_directory="profiles"):
        self.profiles_directory = profiles_directory
        self.profiles = {}
        self.current_profile = None
        self.is_active = False
        self.start_time = None
        self.elapsed_minutes = 0.0
        
        # Ensure profiles directory exists (MicroPython compatible)
        try:
            os.mkdir(profiles_directory)
        except OSError:
            # Directory already exists or other error, continue
            pass
        
        # Load existing profiles
        self.load_all_profiles()
        
        # Create example profiles if none exist
        if not self.profiles:
            self._create_default_profiles()
    
    def _create_default_profiles(self):
        """Create and save default example profiles"""
        example_profiles = create_example_profiles()
        for profile in example_profiles:
            self.save_profile(profile)
        self.load_all_profiles()  # Reload to include saved profiles
    
    def load_all_profiles(self):
        """Load all profiles from the profiles directory"""
        self.profiles.clear()
        
        try:
            # Check if directory exists and list files
            files = os.listdir(self.profiles_directory)
        except OSError:
            # Directory doesn't exist or can't be read
            return
        
        for filename in files:
            if filename.endswith('.json'):
                try:
                    # Construct filepath manually for MicroPython compatibility
                    filepath = self.profiles_directory + '/' + filename
                    profile = TemperatureProfile.load_from_file(filepath)
                    self.profiles[profile.name] = profile
                except Exception as e:
                    print("Error loading profile {}: {}".format(filename, e))
    
    def get_profile_names(self):
        """Get list of available profile names"""
        return list(self.profiles.keys())
    
    def get_profile(self, name):
        """Get profile by name"""
        return self.profiles.get(name)
    
    def save_profile(self, profile):
        """Save a profile to file"""
        try:
            filename = "{}.json".format(profile.name.replace(' ', '_').lower())
            # Construct filepath manually for MicroPython compatibility
            filepath = self.profiles_directory + '/' + filename
            profile.save_to_file(filepath)
            self.profiles[profile.name] = profile
            return True
        except Exception as e:
            print("Error saving profile: {}".format(e))
            return False
    
    def delete_profile(self, name):
        """Delete a profile"""
        try:
            if name in self.profiles:
                filename = "{}.json".format(name.replace(' ', '_').lower())
                # Construct filepath manually for MicroPython compatibility
                filepath = self.profiles_directory + '/' + filename
                try:
                    os.remove(filepath)
                except OSError:
                    # File doesn't exist or can't be deleted
                    pass
                del self.profiles[name]
                
                # If this was the current profile, stop execution
                if self.current_profile and self.current_profile.name == name:
                    self.stop_profile()
                return True
        except Exception as e:
            print("Error deleting profile: {}".format(e))
        return False
    
    def start_profile(self, profile_name):
        """Start executing a profile"""
        profile = self.profiles.get(profile_name)
        if not profile:
            return False
        
        self.current_profile = profile
        self.is_active = True
        self.start_time = time.time()
        self.elapsed_minutes = 0.0
        
        print("Started profile: {}".format(profile_name))
        return True
    
    def stop_profile(self):
        """Stop profile execution"""
        self.is_active = False
        self.current_profile = None
        self.start_time = None
        self.elapsed_minutes = 0.0
        print("Profile execution stopped")
    
    def update(self):
        """
        Update profile execution and return current target temperature
        Returns None if no profile is active
        """
        if not self.is_active or not self.current_profile or not self.start_time:
            return None
        
        # Calculate elapsed time
        current_time = time.time()
        self.elapsed_minutes = (current_time - self.start_time) / 60.0
        
        # Check if profile is complete
        if self.current_profile.is_complete(self.elapsed_minutes):
            print("Profile '{}' completed".format(self.current_profile.name))
            self.stop_profile()
            return None
        
        # Get current target temperature
        phase_index, phase_name, target_temp = self.current_profile.get_current_phase_and_target(self.elapsed_minutes)
        return target_temp
    
    def get_status(self):
        """Get current profile execution status"""
        if not self.is_active or not self.current_profile:
            return {
                'active': False,
                'profile_name': None,
                'current_phase': None,
                'target_temp': None,
                'elapsed_minutes': 0,
                'total_minutes': 0,
                'progress_percent': 0
            }
        
        phase_index, phase_name, target_temp = self.current_profile.get_current_phase_and_target(self.elapsed_minutes)
        progress_percent = min(100, (self.elapsed_minutes / self.current_profile.total_duration) * 100)
        
        return {
            'active': True,
            'profile_name': self.current_profile.name,
            'current_phase': phase_name,
            'current_phase_index': phase_index,
            'total_phases': len(self.current_profile.phases),
            'target_temp': target_temp,
            'elapsed_minutes': self.elapsed_minutes,
            'total_minutes': self.current_profile.total_duration,
            'progress_percent': progress_percent
        }
