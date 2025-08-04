from microdot import Microdot, Response, send_file
import _thread

# Feature flag for profile functionality
ENABLE_PROFILES = True

if ENABLE_PROFILES:
    from profile_manager import ProfileManager

class WebServer:
    def __init__(self, heater):
        self.app = Microdot()
        Response.default_content_type = 'application/json'
        
        self.heater = heater  # Reference to heater for target temp operations
        self.current_temp = 0.0
        self.heater_on = False  # Track heater state
        
        # Initialize profile manager if enabled
        if ENABLE_PROFILES:
            self.profile_manager = ProfileManager()
        else:
            self.profile_manager = None

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
            response = {
                'temp': round(self.current_temp, 1),
                'target': round(self.heater.get_target_temp(), 1),
                'heater_on': self.heater_on,
                'limits': self.heater.get_temp_limits(),
                'profiles_enabled': ENABLE_PROFILES
            }
            
            # Add profile status if enabled
            if ENABLE_PROFILES and self.profile_manager:
                response['profile_status'] = self.profile_manager.get_status()
            
            return response

        @self.app.route('/set_target')
        def set_target(request):
            """ Set the target temperature via query parameter """
            try:
                value = float(request.args.get('value', self.heater.get_target_temp()))
                result = self.heater.set_target_temp(value)
                
                if isinstance(result, tuple):  # Error case
                    return result[0], result[1]
                else:  # Success case
                    return result
            except ValueError:
                return {'status': 'error', 'message': 'Invalid temperature value'}, 400

        # Profile endpoints (only if enabled)
        if ENABLE_PROFILES:
            @self.app.route('/profiles')
            def profiles(request):
                """ Get list of available profiles """
                if not self.profile_manager:
                    return {'status': 'error', 'message': 'Profiles not enabled'}, 404
                
                return {
                    'status': 'ok',
                    'profiles': self.profile_manager.get_profile_names()
                }
            
            @self.app.route('/profile/start')
            def start_profile(request):
                """ Start a profile """
                if not self.profile_manager:
                    return {'status': 'error', 'message': 'Profiles not enabled'}, 404
                
                profile_name = request.args.get('name')
                if not profile_name:
                    return {'status': 'error', 'message': 'Profile name required'}, 400
                
                if self.profile_manager.start_profile(profile_name):
                    return {'status': 'ok', 'message': f'Started profile: {profile_name}'}
                else:
                    return {'status': 'error', 'message': 'Profile not found'}, 404
            
            @self.app.route('/profile/stop')
            def stop_profile(request):
                """ Stop current profile """
                if not self.profile_manager:
                    return {'status': 'error', 'message': 'Profiles not enabled'}, 404
                
                self.profile_manager.stop_profile()
                return {'status': 'ok', 'message': 'Profile stopped'}

    def serve_temperature_once(self, temp):
        """Called from main.py to update the current temperature reading for the web interface"""
        self.current_temp = temp
    
    def serve_heater_state_once(self, heater_on):
        """Called from main.py to update the current heater state for the web interface"""
        self.heater_on = heater_on
    
    def update_profiles(self):
        """Update profile manager and return target temperature if profile is active"""
        if ENABLE_PROFILES and self.profile_manager:
            return self.profile_manager.update()
        return None
