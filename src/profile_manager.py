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
        
        # NEW: Core state variables for the 3-state model
        self.active_profile_name = None  # Which profile is selected/active
        self.is_running = False          # Boolean: is the active profile executing
        self.start_time = None
        self.elapsed_minutes = 0.0
        
        # NEW: Temperature data collection 
        self.temperature_data = []       # Always collected when profile active
        
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
                
                # If this was the active profile, deactivate it
                if self.active_profile_name == name:
                    self.deactivate_profile()
                
                return True
        except Exception as e:
            print("Error deleting profile: {}".format(e))
        return False
    
    def update(self):
        """
        Update profile execution and return current target temperature
        Returns None if no profile is running
        """
        if not self.is_running or not self.active_profile_name or not self.start_time:
            return None
        
        profile = self.profiles.get(self.active_profile_name)
        if not profile:
            print("Error: Active profile '{}' not found".format(self.active_profile_name))
            self.stop_active_profile()
            return None
        
        # Calculate elapsed time
        current_time = time.time()
        self.elapsed_minutes = (current_time - self.start_time) / 60.0
        
        # Check if profile is complete
        if profile.is_complete(self.elapsed_minutes):
            print("Profile '{}' completed after {:.2f} minutes".format(
                self.active_profile_name, self.elapsed_minutes))
            self.stop_active_profile()  # Auto-stop but keep profile active for graph viewing
            return None
        
        # Get current target temperature
        phase_index, phase_name, target_temp = profile.get_current_phase_and_target(self.elapsed_minutes)
        
        # Only print status every 30 seconds to avoid spam
        if int(self.elapsed_minutes * 2) % 60 == 0:  # Every 30 seconds
            print("Profile '{}': {:.1f}min, {}, {:.1f}°C".format(
                self.active_profile_name, self.elapsed_minutes, phase_name, target_temp))
        
        return target_temp
    
    def get_status(self):
        """Get current profile execution status with UI state"""
        # Update elapsed time first if running
        if self.is_running and self.active_profile_name and self.start_time:
            current_time = time.time()
            self.elapsed_minutes = (current_time - self.start_time) / 60.0
        
        # Get profile object if active
        profile = self.profiles.get(self.active_profile_name) if self.active_profile_name else None
        
        if not self.active_profile_name or not profile:
            return {
                # NEW: Core UI state fields
                'active_profile_name': self.active_profile_name,
                'is_running': self.is_running,
                'show_graph': self.show_graph(),
                'show_clear_button': self.show_clear_button(),
                'can_select': self.can_select(),
                'can_create': self.can_create(),
                'can_run': self.can_run(),
                'can_stop': self.can_stop(),
                'can_clear': self.can_clear()
            }
        
        # Get current phase and target if running
        if self.is_running:
            phase_index, phase_name, target_temp = profile.get_current_phase_and_target(self.elapsed_minutes)
        else:
            phase_index, phase_name, target_temp = 0, "Stopped", None
        
        progress_percent = min(100, (self.elapsed_minutes / profile.total_duration) * 100) if profile.total_duration > 0 else 0
        
        return {
            # Core UI state fields  
            'active_profile_name': self.active_profile_name,
            'is_running': self.is_running,
            'show_graph': self.show_graph(),
            'show_clear_button': self.show_clear_button(),
            'can_select': self.can_select(),
            'can_create': self.can_create(),
            'can_run': self.can_run(),
            'can_stop': self.can_stop(),
            'can_clear': self.can_clear(),
            
            # Profile execution fields
            'current_phase': phase_name,
            'current_phase_index': phase_index,
            'total_phases': len(profile.phases),
            'target_temp': target_temp,
            'elapsed_minutes': self.elapsed_minutes,
            'total_minutes': profile.total_duration,
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
    
    # NEW: State query methods for UI
    def show_graph(self):
        """Show graph when any profile is active"""
        return self.active_profile_name is not None
    
    def show_clear_button(self):
        """Show clear button when profile is active but not running"""
        return self.active_profile_name is not None and not self.is_running
    
    def can_select(self):
        """Can select profile when no profile is active"""
        return self.active_profile_name is None
    
    def can_create(self):
        """Can create profile when no profile is active"""
        return self.active_profile_name is None
    
    def can_run(self):
        """Can run when profile is active but not running"""
        return self.active_profile_name is not None and not self.is_running
    
    def can_stop(self):
        """Can stop when profile is active and running"""
        return self.active_profile_name is not None and self.is_running
    
    def can_clear(self):
        """Can clear when profile is active but not running"""
        return self.active_profile_name is not None and not self.is_running
    
    # NEW: State transition methods
    def activate_profile(self, profile_name):
        """Select a profile (make it active but not running)"""
        if profile_name not in self.profiles:
            print("Error: Profile '{}' not found".format(profile_name))
            return False
        
        if self.is_running:
            print("Error: Cannot select profile while another is running")
            return False
        
        # Clear any previous data
        self.clear_temperature_data()
        
        # Set new active profile
        self.active_profile_name = profile_name
        self.is_running = False
        self.start_time = None
        self.elapsed_minutes = 0.0
        
        print("Activated profile: '{}'".format(profile_name))
        return True
    
    def deactivate_profile(self):
        """Clear the active profile (Clear button functionality)"""
        # Note: Caller should stop profile first if needed
        # This is now handled by the clear endpoint
        
        profile_name = self.active_profile_name
        
        # Clear all state
        self.active_profile_name = None
        self.is_running = False
        self.start_time = None
        self.elapsed_minutes = 0.0
        self.clear_temperature_data()
        
        print("Deactivated profile: '{}'".format(profile_name if profile_name else "None"))
        return True
    
    def start_active_profile(self):
        """Start running the currently active profile"""
        if not self.active_profile_name:
            print("Error: No profile is active")
            return False
        
        if self.is_running:
            print("Error: Profile is already running")
            return False
        
        profile = self.profiles[self.active_profile_name]
        
        # Start execution
        self.is_running = True
        self.start_time = time.time()
        self.elapsed_minutes = 0.0
        self.clear_temperature_data()  # Start fresh data collection
        
        print("Started profile: '{}' at time {}".format(self.active_profile_name, self.start_time))
        print("Profile has {} phases, total duration: {} minutes".format(
            len(profile.phases), profile.total_duration))
        return True
    
    def stop_active_profile(self):
        """Stop running the active profile (keep it active for graph viewing)"""
        if not self.is_running:
            print("Error: No profile is running")
            return False
        
        self.is_running = False
        # Keep active_profile_name, start_time, elapsed_minutes, and temperature_data
        # This allows viewing the graph and potentially running again
        
        print("Stopped profile: '{}'".format(self.active_profile_name))
        return True
    
    # NEW: Temperature data collection methods
    def add_temperature_reading(self, temperature):
        """Add temperature reading if profile is active"""
        if not self.active_profile_name:
            return  # No active profile, don't collect data
        
        if not self.start_time:
            return  # No start time set, don't collect data
        
        current_time = time.time()
        elapsed_minutes = (current_time - self.start_time) / 60.0
        
        # Only collect data every 10 seconds to reduce memory usage (0.17 minutes)
        should_record = (len(self.temperature_data) == 0 or 
                        elapsed_minutes - self.temperature_data[-1]['time'] >= 0.15)
        
        if should_record:
            self.temperature_data.append({
                'time': round(elapsed_minutes, 2),
                'temperature': round(temperature, 1)
            })
            
            # Keep only recent data - limit for MicroPython memory
            # Keep last 50 points (about 8-10 minutes of data at 10-second intervals)
            if len(self.temperature_data) > 50:
                self.temperature_data = self.temperature_data[-50:]
    
    def get_temperature_data(self):
        """Get collected temperature data for graphing"""
        return {
            'status': 'ok',
            'data': self.temperature_data,
            'profile_active': self.active_profile_name is not None,
            'profile_running': self.is_running
        }
    
    def clear_temperature_data(self):
        """Clear temperature data (called by deactivate and start)"""
        self.temperature_data = []
