#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse, logging, urllib.parse

description = ''''''

# Initialize argument parsing
class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter): pass
parser = argparse.ArgumentParser(
    epilog=description,
    formatter_class=CustomFormatter,
    description="Server to receive fingerprinting information")

scan_group = parser.add_argument_group('PARAMETERS')
parser.add_argument("-v", "--verbose",  action='store_true', help="Increase output verbosity")

general_group = parser.add_argument_group("NETWORK")
parser.add_argument("-p", "--port", type = int, default=8000, help="Port to listen on")
parser.add_argument("-l", "--listen", type = str, default="127.0.0.1", help="IP to listen on")

args = parser.parse_args()

params = {
    "ip": args.listen,
    "port": args.port
}

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(args.verbose and logging.DEBUG or logging.INFO)
formatter = logging.Formatter('%(levelname)s: [SERVER] %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

temp_fonts = dict()

class AttackerServer(BaseHTTPRequestHandler):
    def do_GET(self):
        # get client ip and url parameters
        client_ip = self.client_address[0]
        url_parameters = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        path = self.path

        self.handle_request(client_ip, url_parameters, path)

    def do_POST(self):
        # get client ip and post data
        client_ip = self.client_address[0]
        content_length = int(self.headers['Content-Length'])
        post_data = urllib.parse.parse_qs(self.rfile.read(content_length).decode('utf-8'))
        path = self.path

        self.handle_request(client_ip, post_data, path)

    def handle_request(self, client_ip:str, parameters:dict, path:str):
        response = ""
        self.send_response(200)

        allowed_files = {
            "/": ("index.html", "text/html"),
            "/index.html": ("index.html", "text/html"),
            "/fingerprint.css": ("fingerprint.css", "text/css"),
        }
        if path in allowed_files:
            response = open(allowed_files[path][0], "r").read()
            # set content type
            self.send_header('Content-type', allowed_files[path][1])
        elif path == "/result":
            logger.info(f"Client {client_ip} requested result") 
            global temp_fonts
            # get length of temp_fonts
            if client_ip in temp_fonts:
                response = str(len(temp_fonts[client_ip]))
                logger.debug(f"Client {client_ip} has {response} fonts")
                del temp_fonts[client_ip]
            self.send_header('Content-type', 'text/plain')
        elif path.startswith("/font/") and "font-name" in parameters:
            font_name = parameters["font-name"][0]
            logger.debug(f"Client {client_ip} requested font {font_name}")
            if client_ip not in temp_fonts:
                temp_fonts[client_ip] = []
            if font_name not in temp_fonts[client_ip]:
                temp_fonts[client_ip].append(font_name)
            self.send_header('Content-type', 'text/plain')
        else:
            self.send_header('Content-type', 'text/plain')

        # respond to client
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

def run( ip: str, port: int, server_class=HTTPServer, handler_class=AttackerServer):
    server_address = (ip, port)
    httpd = server_class(server_address, handler_class)
    logger.debug('Starting http server...')
    logger.info(f"Listening on http://{ip}:{port}")
    httpd.serve_forever()

run(args.listen, args.port)
