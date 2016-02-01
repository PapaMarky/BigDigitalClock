# Copyright 2016, Mark Dyer
import sys
import SocketServer
import logging
import threading

logger = logging.getLogger('BigClock.Server')

running = False
class ClockRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        global running

        while True:
            try:
                data = self.request.recv(1024)
                cur_thread = threading.current_thread()
                logger.info('%s: handling message: "%s"', cur_thread, str(data))
            except:
                logger.error("Exception on %s '%s'", threading.current_thread().name, sys.exc_info()[0])
                return
            logger.debug("Got '%s'", str(data))
            if data == 'shutdown':
                running = False
                logger.debug("Shutdown: server: %s", str(ClockServer.server))
                if ClockServer.server is not None:
                    logger.debug("Whacking server in head")
                    ClockServer.server.shutdown()
                return
            if data == 'done':
                return

class ClockServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    server = None

    def __init__(self, master, a, b):
        SocketServer.TCPServer.__init__(self, a, b)
        ClockServer.server = master
        


