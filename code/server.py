import socket
import uselect

class WebServer:
    def __init__(self, port=80):
        self.addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # avoid OSError: [Errno 98] EADDRINUSE
        self.server.bind(self.addr)
        self.server.listen(1)
        self.poller = uselect.poll()
        self.poller.register(self.server, uselect.POLLIN)
        print("Web server listening on port", port)

    def serve_once(self, temp):
        try:
            # Only accept if a connection is pending
            if self.poller.poll(0):  # 0 = non-blocking poll
                client, addr = self.server.accept()
                print("Client connected:", addr)
                request = client.recv(1024)
                # Prepare response
                response = self.build_response(temp)
                client.send(response.encode())
                client.close()
        except Exception as e:
            print("Web server error:", e)

    def build_response(self, temp):
        value = "{:.1f}".format(temp if temp is not None else 0.0)

        html = "<!DOCTYPE html>\n"
        html += "<html>\n"
        html += "  <head>\n"
        html += "    <title>Pico W</title>\n"
        html += '      <meta http-equiv="refresh" content="2">\n'
        html += "  </head>\n"
        html += "  <body><h1>T: {} &deg;C</h1></body>\n".format(value)
        html += "</html>"

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n"
            "Content-Length: {}\r\n"
            "\r\n".format(len(html))
        )
        response += html
        return response


