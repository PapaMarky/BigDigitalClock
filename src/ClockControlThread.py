# Copyright 2016, Mark Dyer
import threading
import ClockConfig as config
import ClockServer as server
import logging

logger = logging.getLogger('BigClock.ControlThread')

VALID_REQUESTS = ['shutdown', 'brightness']

class ClockControlThread(threading.Thread):
    def __init__(self, control_q, display_q):
        super(ClockControlThread, self).__init__(name='ControlThread')
        self.control_q = control_q
        self.display_q = display_q
        self.running = True

    def queue_task(self, task):
        self.control_q.put(task)

    def shutdown(self):
        logger.info('shutdown')
        logger.debug('Active Count: %s', threading.active_count())
        self.running = False

    def handle_request(self, request):
        logger.info("Message From '%s': '%s'", request['connection'].thread.name, str(request))
        tokens = request['msg']
        if tokens[0] in VALID_REQUESTS:
            self.display_q.put(request)
        else:
            logger.error("bad request: '%s'", tokens[0])

    def handle_response(self, response):
        logger.debug("handle_response %s", str(response))
        connection = response['connection']
        connection.queue_task(response)

    def handle_job(self, job):
        logger.debug("handle_job %s", str(job))
        if job.has_key('type'):
            if job['type'] == 'request':
                self.handle_request(job)
            if job['type'] == 'response':
                self.handle_response(job)


    def run(self):
        logger.info("ClockControlThread Starting")
        self.config = config.ClockConfig('/var/BigClock/config.json')

        HOST, PORT = 'localhost', 60969

        logger.info("ClockControlThread Starting Server")
        self.server = server.ClockServer(self, HOST, PORT)
        self.server.start()

        logger.info("Server running in thread '%s'", self.server.name)

        while self.running:
            # check the job queue
            while not self.control_q.empty():
                job = self.control_q.get()
                logger.debug('Got a Job: %s', str(job))
                logger.debug('Active Count: %s', threading.active_count())
                self.handle_job(job)
            # check the server

        server.ClockServer.controller = None
        self.server.shutdown()
