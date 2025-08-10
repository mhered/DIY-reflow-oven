"""
Profile Manager for Temperature Control
Manages profile execution and integration with heater control
"""

import os
import time
from profile import TemperatureProfile, TemperaturePhase, create_example_profiles, debug_print


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
        print("Created {} default profiles".format(len(example_profiles)))
    
    def load_all_profiles(self):
        """Load all profiles from the profiles directory"""
        debug_print("Loading profiles from: {}".format(self.profiles_directory))
        
        old_count = len(self.profiles)
        debug_print("Currently have {} profiles loaded".format(old_count))
        
        try:
            # Check if directory exists and list files
            files = os.listdir(self.profiles_directory)
            debug_print("Directory listing successful: {} files".format(len(files)))
            
            json_files = [f for f in files if f.endswith('.json')]
            debug_print("JSON files found: {}".format(len(json_files)))
            
            # Now clear and reload
            self.profiles.clear()
            debug_print("Cleared profiles dictionary")
            
            loaded_count = 0
            for filename in json_files:
                try:
                    filepath = self.profiles_directory + '/' + filename
                    profile = TemperatureProfile.load_from_file(filepath)
                    self.profiles[profile.name] = profile
                    loaded_count += 1
                except Exception as e:
                    print("Error loading {}: {}".format(filename, e))
            
            print("Successfully loaded {} profiles".format(loaded_count))
            
        except Exception as e:
            print("CRITICAL ERROR in load_all_profiles: {}".format(e))
            # If there's an error, don't clear the existing profiles
            return
    
    def get_profile_names(self):
        """Get list of available profile names"""
        return list(self.profiles.keys())
    
    def get_profile(self, name):
        """Get profile by name"""
        return self.profiles.get(name)
    
    def debug_file_system(self):
        """Debug helper to check file system state"""
        debug_print("=== Profile Manager Debug Info ===")
        debug_print("Profiles directory: {}".format(self.profiles_directory))
        debug_print("Loaded profiles: {}".format(list(self.profiles.keys())))
        
        try:
            # Force sync before listing
            if hasattr(os, 'sync'):
                os.sync()
            files = os.listdir(self.profiles_directory)
            debug_print("Files in directory: {}".format(files))
            json_files = [f for f in files if f.endswith('.json')]
            debug_print("JSON files: {}".format(json_files))
        except Exception as e:
            debug_print("Error listing directory: {}".format(e))
            files = []
        debug_print("=== End Debug Info ===")
        
        return {
            'loaded_profiles': list(self.profiles.keys()),
            'directory_files': files
        }
    
    def save_profile(self, profile):
        """Save a profile to file"""
        try:
            profile.save_to_file(self.profiles_directory)
            
            # Force file system sync on MicroPython
            try:
                if hasattr(os, 'sync'):
                    os.sync()
            except Exception:
                pass  # Ignore if sync is not available
            
            # Add to in-memory profiles dictionary directly
            self.profiles[profile.name] = profile
            print("Saved profile: {}".format(profile.name))
            
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
                    
                    # Force file system sync on MicroPython
                    try:
                        if hasattr(os, 'sync'):
                            os.sync()
                    except Exception:
                        pass  # Ignore if sync is not available
                        
                except OSError:
                    # File doesn't exist or can't be deleted
                    pass
                
                # Remove from in-memory profiles dictionary directly
                del self.profiles[name]
                print("Deleted profile: {}".format(name))
                
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
            print("Error: Profile '{}' not found".format(profile_name))
            return False
        
        self.current_profile = profile
        self.is_active = True
        self.start_time = time.time()
        self.elapsed_minutes = 0.0
        
        print("Started profile: '{}' at time {}".format(profile_name, self.start_time))
        print("Profile has {} phases, total duration: {} minutes".format(
            len(profile.phases), profile.total_duration))
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
            print("Profile '{}' completed after {:.2f} minutes".format(
                self.current_profile.name, self.elapsed_minutes))
            self.stop_profile()
            return None
        
        # Get current target temperature
        phase_index, phase_name, target_temp = self.current_profile.get_current_phase_and_target(self.elapsed_minutes)
        # Only print status every 30 seconds to avoid spam
        if int(self.elapsed_minutes * 2) % 60 == 0:  # Every 30 seconds
            print("Profile '{}': {:.1f}min, {}, {:.1f}°C".format(
                self.current_profile.name, self.elapsed_minutes, phase_name, target_temp))
        return target_temp
    
    def get_status(self):
        """Get current profile execution status"""
        # Update elapsed time first
        if self.is_active and self.current_profile and self.start_time:
            current_time = time.time()
            self.elapsed_minutes = (current_time - self.start_time) / 60.0
        
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
    
    def create_profile(self, name, phases_data):
        """Create a new temperature profile from phase data"""
        try:
            debug_print("Creating profile: {}".format(name))
            debug_print("Phases data: {}".format(phases_data))
            
            # Create phases from data
            phases = []
            for phase_data in phases_data:
                phase = TemperaturePhase(
                    name=phase_data['name'],
                    start_temp=float(phase_data['start_temp']),
                    end_temp=float(phase_data['end_temp']),
                    duration_minutes=float(phase_data['duration_minutes'])
                )
                phases.append(phase)
            
            # Create profile
            profile = TemperatureProfile(name, phases)
            debug_print("Profile created with {} phases".format(len(phases)))
            
            # Use the existing save_profile method instead of duplicating logic
            success = self.save_profile(profile)
            if success:
                print("Profile '{}' saved successfully".format(name))
            else:
                print("Failed to save profile '{}'".format(name))
                
            return success
            
        except Exception as e:
            print("Error creating profile '{}': {}".format(name, e))
            return False

    def get_profile_graph_data(self, profile_name):
        """Get profile data formatted for graphing"""
        if profile_name not in self.profiles:
            return None
            
        profile = self.profiles[profile_name]
        
        # Generate temperature points - very reduced frequency to save memory on MicroPython
        points = []
        total_minutes = 0.0
        
        for phase in profile.phases:
            phase_start_time = total_minutes
            # Very conservative sampling for MicroPython memory constraints
            # Maximum 3-4 points per phase to keep total points low
            if phase.duration_minutes <= 2:
                num_samples = 2  # Start and end only for very short phases
            elif phase.duration_minutes <= 10:
                num_samples = 3  # Start, middle, end
            else:
                num_samples = 4  # Start, 1/3, 2/3, end
            
            for i in range(num_samples):
                if num_samples == 1:
                    time_in_phase = phase.duration_minutes
                else:
                    time_in_phase = (i / (num_samples - 1)) * phase.duration_minutes
                    
                absolute_time = phase_start_time + time_in_phase
                temp = phase.get_target_temp(time_in_phase)
                
                points.append({
                    'time': round(absolute_time, 2),
                    'temperature': round(temp, 1),
                    'phase': phase.name
                })
                    
            total_minutes += phase.duration_minutes
        
        return {
            'name': profile.name,
            'total_duration': round(total_minutes, 2),
            'points': points
        }
