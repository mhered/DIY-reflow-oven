from microdot import Microdot, Response, send_file
import _thread

class WebServer:
    def __init__(self):
        self.app = Microdot()
        Response.default_content_type = 'application/json'

        self.current_temp = 0.0
        self.target_temp = 25.0  # Default value
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
                'target': round(self.target_temp, 1),
                'heater_on': self.heater_on
            }

        @self.app.route('/set_target')
        def set_target(request):
            """ Set the target temperature via query parameter """
            try:
                value = float(request.args.get('value', self.target_temp))
                self.target_temp = value
                print(f"Target temperature set to {self.target_temp}")
                return {'status': 'ok', 'target': self.target_temp}
            except:
                return {'status': 'error'}, 400

    def serve_temperature_once(self, temp):
        """Called from main.py to update the current temperature reading for the web interface"""
        self.current_temp = temp
    
    def serve_heater_state_once(self, heater_on):
        """Called from main.py to update the current heater state for the web interface"""
        self.heater_on = heater_on
