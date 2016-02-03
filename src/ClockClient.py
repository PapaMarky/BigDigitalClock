# copyright 2016, Mark Dyer
import sys
import socket
import errno
import logging
import json
from ClockMessage import create_request

class ClockClient:
    CLIENT_LIST = []

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name + '.client')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('127.0.0.1', 60969))
        self.sock.settimeout(0)
        ClockClient.CLIENT_LIST.append(self)

    def send_message(self, msg):
        self.logger.info('send_message "%s"', msg)
        try:
            self.sock.sendall(json.dumps(msg))
        except:
            self.logger.error("Exception: '%s'", sys.exc_info()[0])

    def check_for_message(self):
        try:
            msg = self.sock.recv(1024)
        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                return None
            else:
                self.logger.error("check_for_message Exception: %s", e)
                return None
        self.logger.debug("Got Message: %s", msg)
        return msg

    def send_shutdown(self):
        message = create_request(self.name, ['shutdown'])
        self.send_message(message)

    def shutdown(self):
        self.logger.info('shutdown')
        self.sock.close()

    def shutdown_server(self):
        self.logger.info('shutdown_server')
        self.send_message('shutdown')

    def set_brightness(self, b):
        self.logger.info('set_brightness %s', b)
        if b > 100:
            b = 100
        if b < 0:
            b = 0
        message = create_request(self.name, ['brightness', b])
        self.send_message(message)

