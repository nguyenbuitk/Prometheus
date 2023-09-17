import http.server
import random
from prometheus_client import start_http_server, Counter, Gauge
import time

REQUEST_INPROGRESS = Gauge('app_requests_inprogress',
                           'number of application requests in porgress')

APP_PORT = 8000
METRICS_PORT = 8001


class HandleRequests(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        REQUEST_INPROGRESS.inc()
        time.sleep(5)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>First Application</title></head><body style='color: #333; margin-top: 30px;'><center><h2>Welcome to our first Prometheus-Python application.</center></h2></body></html>", "utf-8"))
        self.wfile.close()
        REQUEST_INPROGRESS.dec()
if __name__ == "__main__":
	start_http_server(METRICS_PORT)
	server = http.server.HTTPServer(('localhost', APP_PORT), HandleRequests)
	server.serve_forever()
