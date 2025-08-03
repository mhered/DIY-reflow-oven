from microdot import Microdot, Response, send_file
import _thread

class WebServer:
    def __init__(self):
        self.app = Microdot()
        Response.default_content_type = 'application/json'

        self.current_temp = 0.0
        self.target_temp = 25.0  # Default value

        self.setup_routes()

        # Start web server in background thread
        _thread.start_new_thread(self.app.run, (), {'host': '0.0.0.0', 'port': 80})

    def setup_routes(self):
        @self.app.route('/')
        def index(request):
            return send_file('static/index.html')

        @self.app.route('/style.css')
        def style(request):
            return send_file('static/style.css')

        @self.app.route('/temperature')
        def temperature(request):
            heater_on = self.current_temp < self.target_temp - 1.0  # 1°C margin
            return {
                'temp': round(self.current_temp, 1),
                'target': round(self.target_temp, 1),
                'heater_on': heater_on
            }

        @self.app.route('/set_target')
        def set_target(request):
            try:
                value = float(request.args.get('value', self.target_temp))
                self.target_temp = value
                print(f"Target temperature set to {self.target_temp}")
                return {'status': 'ok', 'target': self.target_temp}
            except:
                return {'status': 'error'}, 400

    def serve_once(self, temp):
        """Called from main.py to update the current temperature reading"""
        self.current_temp = temp
