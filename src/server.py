from microdot import Microdot, Response, send_file
import _thread
from profile_manager import ProfileManager

class WebServer:
    def __init__(self, heater):
        self.app = Microdot()
        Response.default_content_type = 'application/json'
        
        self.heater = heater  # Reference to heater for target temp operations
        self.current_temp = 0.0
        self.heater_on = False  # Track heater state
        
        # Initialize profile manager
        self.profile_manager = ProfileManager()

        self.setup_routes()

        # Start web server in background thread
        _thread.start_new_thread(self.app.run, (), {'host': '0.0.0.0', 'port': 80})
    
    def url_decode(self, encoded_string):
        """URL decode a string - MicroPython compatible"""
        try:
            # Handle common URL encodings manually
            decoded = encoded_string.replace('%20', ' ')  # Space
            decoded = decoded.replace('%21', '!')         # Exclamation mark
            decoded = decoded.replace('%22', '"')         # Quote
            decoded = decoded.replace('%23', '#')         # Hash
            decoded = decoded.replace('%24', '$')         # Dollar
            decoded = decoded.replace('%25', '%')         # Percent
            decoded = decoded.replace('%26', '&')         # Ampersand
            decoded = decoded.replace('%27', "'")         # Apostrophe
            decoded = decoded.replace('%28', '(')         # Left parenthesis
            decoded = decoded.replace('%29', ')')         # Right parenthesis
            decoded = decoded.replace('%2A', '*')         # Asterisk
            decoded = decoded.replace('%2B', '+')         # Plus
            decoded = decoded.replace('%2C', ',')         # Comma
            decoded = decoded.replace('%2D', '-')         # Hyphen
            decoded = decoded.replace('%2E', '.')         # Period
            decoded = decoded.replace('%2F', '/')         # Forward slash
            return decoded
        except:
            return encoded_string  # Return original if decoding fails

    def setup_routes(self):
        @self.app.route('/')
        def index(request):
            """ Serve the main HTML page """
            return send_file('static/index.html')

        @self.app.route('/style.css')
        def style(request):
            """ Serve CSS file for styling the web interface """
            return send_file('static/style.css')

        @self.app.route('/temperature')
        def temperature(request):
            """ Get current, target temperature and heater state with UI state """
            target_temp = self.heater.get_target_temp()
            status = self.profile_manager.get_status()
            
            response = {
                'temp': round(self.current_temp, 1),
                'target': round(target_temp, 1) if target_temp is not None else None,
                'heater_on': self.heater_on,
                'ui_state': status  # Complete UI state from ProfileManager
            }
            
            return response

        # Profile endpoints
        @self.app.route('/profiles')
        def profiles(request):
            """ Get list of available profiles """
            return {
                'status': 'ok',
                'profiles': self.profile_manager.get_profile_names()
            }
        @self.app.route('/profile/<profile_name>/activate', methods=['POST'])
        def activate_profile(request, profile_name):
            """ Activate a profile for execution """
            try:
                # URL decode the profile name to handle spaces and special characters
                decoded_name = self.url_decode(profile_name)
                
                success = self.profile_manager.activate_profile(decoded_name)
                if success:
                    return {'status': 'ok', 'message': f'Profile {decoded_name} activated'}
                else:
                    return {'status': 'error', 'message': f'Failed to activate profile {decoded_name}'}, 400
            except ValueError as e:
                return {'status': 'error', 'message': str(e)}, 400        @self.app.route('/profile/deactivate', methods=['POST'])
        def deactivate_profile(request):
            """ Deactivate the currently active profile """
            try:
                self.profile_manager.deactivate_profile()
                return {'status': 'ok', 'message': 'Profile deactivated'}
            except ValueError as e:
                return {'status': 'error', 'message': str(e)}, 400
        
        @self.app.route('/profile/<profile_name>/start', methods=['POST'])
        def start_profile(request, profile_name):
            """ Start running the active profile """
            try:
                # URL decode the profile name to handle spaces and special characters
                decoded_name = self.url_decode(profile_name)
                
                # First activate if needed
                if self.profile_manager.active_profile_name != decoded_name:
                    self.profile_manager.activate_profile(decoded_name)
                
                # Then start running
                self.profile_manager.start_active_profile()
                
                return {'status': 'ok', 'message': f'Profile {decoded_name} started'}
            except ValueError as e:
                return {'status': 'error', 'message': str(e)}, 400
        
        @self.app.route('/profile/stop', methods=['POST'])
        def stop_profile(request):
            """ Stop the currently running profile """
            try:
                self.profile_manager.stop_active_profile()
                return {'status': 'ok', 'message': 'Profile stopped'}
            except ValueError as e:
                return {'status': 'error', 'message': str(e)}, 400
        
        @self.app.route('/clear-graph-data', methods=['POST'])
        def clear_graph_data(request):
            """ Clear temperature data for graph (called by Clear button) """
            try:
                self.profile_manager.clear_temperature_data()
                return {'status': 'ok', 'message': 'Graph data cleared'}
            except Exception as e:
                print("Error clearing graph data: {}".format(e))
                return {'status': 'error', 'message': 'Failed to clear graph data'}, 500
        
        @self.app.route('/profile/clear', methods=['POST'])
        def clear_profile(request):
            """ Complete clear operation: stop profile if running, clear data, deactivate """
            try:
                # If profile is running, stop it first
                if self.profile_manager.is_running:
                    self.profile_manager.stop_active_profile()
                
                # Clear temperature data
                self.profile_manager.clear_temperature_data()
                
                # Deactivate profile
                self.profile_manager.deactivate_profile()
                
                return {'status': 'ok', 'message': 'Profile cleared successfully'}
            except Exception as e:
                print("Error clearing profile: {}".format(e))
                return {'status': 'error', 'message': 'Failed to clear profile'}, 500
        
        @self.app.route('/profile/data')
        def get_profile_data(request):
            """ Get profile data for graphing """
            try:
                profile_name = request.args.get('name')
                if not profile_name:
                    return {'status': 'error', 'message': 'Profile name required'}, 400
                
                # URL decode the profile name to handle spaces and special characters
                decoded_name = self.url_decode(profile_name)
                
                # Get profile data from profile manager
                profile_data = self.profile_manager.get_profile_graph_data(decoded_name)
                if profile_data:
                    return {'status': 'ok', 'data': profile_data}
                else:
                    return {'status': 'error', 'message': 'Profile not found'}, 404
            except Exception as e:
                print("Error in profile/data endpoint: {}".format(e))
                return {'status': 'error', 'message': 'Server error'}, 500
        
        @self.app.route('/temperature/data')
        def get_temperature_data(request):
            """ Get temperature data for graphing """
            try:
                # Use ProfileManager's temperature data
                if self.profile_manager.active_profile_name:
                    temp_data_response = self.profile_manager.get_temperature_data()
                    return {
                        'status': 'ok',
                        'data': temp_data_response['data'],  # Extract the actual data array
                        'profile_active': True,
                        'profile_name': self.profile_manager.active_profile_name,
                        'is_running': self.profile_manager.is_running
                    }
                else:
                    return {
                        'status': 'ok',
                        'data': [],
                        'profile_active': False,
                        'profile_name': '',
                        'is_running': False
                    }
            except Exception as e:
                print("Error in temperature/data endpoint: {}".format(e))
            
        @self.app.route('/profile/create')
        def create_profile(request):
            """ Create a new profile """
            # Get individual parameters for MicroPython URL length limits
            profile_name = request.args.get('name')
            if not profile_name:
                return {'status': 'error', 'message': 'Profile name required'}, 400
            
            # URL decode the profile name to handle spaces and special characters
            decoded_name = self.url_decode(profile_name)
            
            # Collect phase data from multiple parameters
            phases_data = []
            phase_index = 0
            
            while True:
                phase_name = request.args.get('phase_{}_name'.format(phase_index))
                if not phase_name:  # No more phases
                    break
                
                try:
                    start_temp = float(request.args.get('phase_{}_start'.format(phase_index), 0))
                    end_temp = float(request.args.get('phase_{}_end'.format(phase_index), 0))
                    duration = float(request.args.get('phase_{}_duration'.format(phase_index), 0))
                    
                    phases_data.append({
                        'name': phase_name,
                        'start_temp': start_temp,
                        'end_temp': end_temp,
                        'duration_minutes': duration
                    })
                    
                    phase_index += 1
                    
                except (ValueError, TypeError):
                    return {'status': 'error', 'message': 'Invalid phase data for phase {}'.format(phase_index)}, 400
            
            if not phases_data:
                return {'status': 'error', 'message': 'At least one phase required'}, 400
            
            try:
                # Create profile
                if self.profile_manager.create_profile(decoded_name, phases_data):
                    # Give file system time to sync (especially important on MicroPython)
                    import time
                    time.sleep(0.1)
                    return {'status': 'ok', 'message': 'Profile created successfully'}
                else:
                    return {'status': 'error', 'message': 'Failed to create profile'}, 500
                    
            except Exception as e:
                return {'status': 'error', 'message': 'Error creating profile: {}'.format(str(e))}, 400

    def serve_temperature_once(self, temp):
        """Called from main.py to update the current temperature reading for the web interface"""
        self.current_temp = temp
        
        # Let ProfileManager handle temperature data collection
        self.profile_manager.add_temperature_reading(temp)
    
    def serve_heater_state_once(self, heater_on):
        """Called from main.py to update the current heater state for the web interface"""
        self.heater_on = heater_on
    
    def update_profiles(self):
        """Update profile manager and return target temperature if profile is active"""
        return self.profile_manager.update()
