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
            """ Get current, target temperature and heater state """
            target_temp = self.heater.get_target_temp()
            response = {
                'temp': round(self.current_temp, 1),
                'target': round(target_temp, 1) if target_temp is not None else None,
                'heater_on': self.heater_on
            }
            
            # Add profile status
            response['profile_status'] = self.profile_manager.get_status()
            
            return response

        # Profile endpoints
        @self.app.route('/profiles')
        def profiles(request):
            """ Get list of available profiles """
            return {
                'status': 'ok',
                'profiles': self.profile_manager.get_profile_names()
            }
        @self.app.route('/profile/start')
        def start_profile(request):
            """ Start a profile """
            profile_name = request.args.get('name')
            if not profile_name:
                return {'status': 'error', 'message': 'Profile name required'}, 400
            
            if self.profile_manager.start_profile(profile_name):
                return {'status': 'ok', 'message': 'Started profile: {}'.format(profile_name)}
            else:
                return {'status': 'error', 'message': 'Profile not found'}, 404
        
        @self.app.route('/profile/stop')
        def stop_profile(request):
            """ Stop current profile """
            self.profile_manager.stop_profile()
            # Set heater target to None when profile is stopped
            self.heater.set_target_temp(None)
            return {'status': 'ok', 'message': 'Profile stopped'}
        @self.app.route('/profile/create')
        def create_profile(request):
            """ Create a new profile """
            # Get individual parameters for MicroPython URL length limits
            profile_name = request.args.get('name')
            if not profile_name:
                return {'status': 'error', 'message': 'Profile name required'}, 400
            
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
                if self.profile_manager.create_profile(profile_name, phases_data):
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
    
    def serve_heater_state_once(self, heater_on):
        """Called from main.py to update the current heater state for the web interface"""
        self.heater_on = heater_on
    
    def update_profiles(self):
        """Update profile manager and return target temperature if profile is active"""
        return self.profile_manager.update()
