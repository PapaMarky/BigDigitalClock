# copyright 2016, Mark Dyer
import sys
import socket
import errno
import logging
import json
from ClockMessage import create_request
from ClockMessage import VALID_COMMANDS
from ClockMessage import VALID_CONFIGS
from ClockMessage import VALID_MODES

class ClockClient:
    CLIENT_LIST = []

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name + '.client')

        self.connected = False
        self.connect_to_server()

        ClockClient.CLIENT_LIST.append(self)
        self.running = True
        self.command_handlers = {
            'get': self.handle_get,
            'set': self.handle_set,
            'shutdown': self.handle_shutdown
            }
        self.internal_msg_queue = []

    def send_internal_message(self, msg):
        self.internal_msg_queue.insert(0, json.dumps(msg))

    def is_connected(self):
        return self.connected

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(('127.0.0.1', 60969))
            self.sock.settimeout(1)
            self.connected = True
        except socket.error, e:
            self.connected = False
            self.logger.warning('Server Connection Failed')

    def send_message(self, msg):
        self.logger.info('send_message "%s"', msg)
        try:
            self.sock.sendall(json.dumps(msg))
        except:
            self.logger.error("Exception: '%s'", sys.exc_info()[0])

    def check_for_message(self):
        msg = None
        if len(self.internal_msg_queue) >= 1:
            msg = self.internal_msg_queue.pop()
            return msg

        if not self.connected:
            self.connect_to_server()
            if not self.connected:
                return None
            self.send_internal_message({'type': 'response', 'status': 'OK', 'msg': ['connect']})
        try:
            msg = self.sock.recv(1024)
        except socket.timeout, e:
            err = e.args[0]
            if err == 'timed out':
                return None
            else:
                self.logger.error("check_for_message Exception: %s", e)
                # should exit
                self.shutdown()
                sys.exit(1)
        except socket.error, e:
            self.logger.error("check_for_message Exception: %s", e)
            # should exit
            self.shutdown()
            sys.exit(2)
        else:
            if len(msg) == 0:
                self.logger.info("Server has closed.")
                # should exit
                self.shutdown()
            else:
                self.logger.debug("Got Message: %s", msg)
        return msg

    def send_shutdown(self):
        message = create_request(self.name, ['shutdown'])
        self.send_message(message)

    def shutdown(self):
        self.logger.info('shutdown')
        self.sock.close()
        self.running = False

    def shutdown_server(self):
        self.logger.info('shutdown_server')
        self.send_message('shutdown')

    # command handlers
    def handle_shutdown(self, msg):
        self.send_shutdown()

    def handle_get(self, msg):
        message = create_request(self.name, msg)
        self.send_message(message)

    def handle_set(self, msg):
        message = create_request(self.name, msg)
        self.send_message(message)

    def handle_request(self, msg):
        if type(msg) == str:
            msg = msg.split()

        self.logger.info("Msg: %s", str(msg))
        if len(msg) <= 0:
            self.logger.warning("Empty input")
            return (False, "Empty Request")

        # special client messages
        if msg[0] == 'connect':
            if self.connected:
               return (False, "Already Connected")
            self.connect_to_server()
            if self.connected:
                return (True, "Connected to Server")
            else:
                return (False, "Connection Failed")

        if not self.connected:
            return (False, 'Not Connected to Server')

        if msg[0] in self.command_handlers:
            self.command_handlers[msg[0]](msg)
            return (True, 'Request Sent')
        else:
            self.logger.warn('Unknown command: "%s"', msg[0])
            return (False, 'Unknown Command: {}'.format(msg[0]))
        
