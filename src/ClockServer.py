# Copyright 2016, Mark Dyer
import sys
import SocketServer
import ClockClient
import logging
import threading

logger = logging.getLogger('BigClock.Server')

running = False
class ClockRequestHandler(SocketServer.BaseRequestHandler):
    handlers = []

    def setup(self):
        if ClockRequestHandler.handlers is not None:
            ClockRequestHandler.handlers.append(self)

    def finish(self):
        if ClockRequestHandler.handlers is not None:
            ClockRequestHandler.handlers.remove(self)

    def handle(self):
        global running

        running = True
        while running:
            try:
                data = self.request.recv(1024)
                cur_thread = threading.current_thread()
                logger.debug("Got '%s'", str(data))
                if ClockServer.controller is not None:
                    ClockServer.controller.handle(self, cur_thread, data)
                
            except:
                logger.error("Exception on %s '%s'", threading.current_thread().name, sys.exc_info()[0])
                return

            if data == 'shutdown':
                running = False
                logger.debug("Shutdown: server: %s", str(ClockServer.controller))
                ClockServer.controller.shutdown()
                return
            if data == 'done':
                return

class ClockServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    controller = None

    def __init__(self, controller, a, b):
        SocketServer.TCPServer.__init__(self, a, b)
        ClockServer.controller = controller
        
    def notify_all(self, sender, msg):
        for handler in ClockRequestHandler.handlers:
            handler.request.sendall(msg)

