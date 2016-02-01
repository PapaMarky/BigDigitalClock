# copyright 2016, Mark Dyer
import sys
import socket
import logging

class ClockClient:
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name + '.client')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', 60969))
        self.sock.settimeout(0)

    def send_message(self, msg):
        try:
            self.sock.sendall(msg)
        except:
            self.logger.error("Exception: '%s'", sys.exc_info()[0])

    def shutdown(self):
        self.sock.close()

    def shutdown_server(self):
        self.send_message('shutdown')

    def set_brightness(self, b):
        if b > 100:
            b = 100
        if b < 0:
            b = 0
        message = 'set_brightness:{}'.format(b)
        self.send_message(message)

