# Copyright 2016, Mark Dyer
import threading
import ClockConfig as config
import ClockServer as server
import logging

logger = logging.getLogger('BigClock.ControlThread')

class ClockControlThread(threading.Thread):
    def __init__(self, control_q, display_q):
        super(ClockControlThread, self).__init__()
        self.control_q = control_q
        self.display_q = display_q
        self.running = True

    def shutdown(self):
        logger.info('shutdown')
        self.running = False
        self.display_q.put('shutdown')

    def handle(self, handler, thread, data):
        logger.info("Message From '%s': '%s'", thread.name, str(data))

        if data == 'shutdown':
            self.shutdown()
            return

        tokens = data.split(':')
        if tokens[0] == 'brightness':
            b = int(tokens[1])
            logger.info("Setting Brightness to %d", b)
            self.display_q.put(tokens)

    def run(self):
        logger.info("ClockControlThread Starting")
        self.config = config.ClockConfig('/var/BigClock/config.json')

        HOST, PORT = 'localhost', 60969

        self.server = server.ClockServer(self, (HOST, PORT), server.ClockRequestHandler)
        ip, port = self.server.server_address
        logger.info("Created Server: %s : %s", ip, port)
        self.server_thread = threading.Thread(target= self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info("Server running in thread '%s'", self.server_thread.name)

        while self.running:
            # check the job queue
            while not self.control_q.empty():
                job = self.control_q.get()
                logger.debug('Got a Job: %s', str(job))
            
            # check the server
        
        self.server.shutdown()
        self.server.server_close()
