import socket

class WebServer:
    def __init__(self, port=80):
        self.addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
        self.server = socket.socket()
        self.server.bind(self.addr)
        self.server.listen(1)
        print("🌐 Web server listening on port", port)

    def serve_once(self, temp):
        try:
            client, addr = self.server.accept()
            print("📲 Client connected:", addr)

            request = client.recv(1024)

            # Prepare response
            response = self.build_response(temp)
            client.send(response)
            client.close()
        except Exception as e:
            print("⚠️ Web server error:", e)

    def build_response(self, temp):
        html = "HTTP/1.0 200 OK\r\nContent-Type: text/html\r\n\r\n"
        html += "T: {:.1f} ºC".format(temp if temp is not None else 0.0)
        return html
