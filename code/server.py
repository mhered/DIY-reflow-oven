from microdot import Microdot, Response, send_file
import _thread

class WebServer:
    def __init__(self, heater):
        self.app = Microdot()
        Response.default_content_type = 'application/json'
        
        self.heater = heater  # Reference to heater for target temp operations
        self.current_temp = 0.0
        self.heater_on = False  # Track heater state

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
            return {
                'temp': round(self.current_temp, 1),
                'target': round(self.heater.get_target_temp(), 1),
                'heater_on': self.heater_on,
                'limits': self.heater.get_temp_limits()
            }

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

    def serve_temperature_once(self, temp):
        """Called from main.py to update the current temperature reading for the web interface"""
        self.current_temp = temp
    
    def serve_heater_state_once(self, heater_on):
        """Called from main.py to update the current heater state for the web interface"""
        self.heater_on = heater_on
