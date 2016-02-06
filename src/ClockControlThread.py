# Copyright 2016, Mark Dyer
import threading
import ClockConfig as config
import ClockServer as server
import logging
import copy

logger = logging.getLogger('BigClock.ControlThread')

VALID_REQUESTS = ['shutdown', 'brightness']

class ClockControlThread(threading.Thread):
    def __init__(self, control_q, display_q):
        super(ClockControlThread, self).__init__(name='ControlThread')
        self.control_q = control_q
        self.display_q = display_q
        self.running = True
        self.finished = False
        self.response_handlers = {
            'shutdown':   self.resp_shutdown,
            'brightness': self.resp_brightness,
            'mode':       self.resp_mode
            }

    def stop(self):
        logger.info('stop() called')
        self.running = False

    def queue_task(self, task):
        self.control_q.put(task)

    def shutdown(self):
        logger.info('shutdown')
        self.server.shutdown()
        self.stop()

    def handle_request(self, request):
        logger.info("Message From '%s': '%s'", request['connection'].thread.name, str(request))
        tokens = request['msg']
        if tokens[0] in VALID_REQUESTS:
            self.display_q.put(request)
        else:
            logger.error("bad request: '%s'", tokens[0])
            connection = request['connection']
            request['type'] = 'response'
            request['status'] = 'BAD REQUEST'
            connection.queue_task(request)

    def resp_ignore(self, response):
        logger.info('Ignoring response: %s', str(response))

    def resp_shutdown(self, response):
        logger.info('handle shutdown response')

    def resp_mode(self, response):
        logger.info('handle mode response')

    def resp_brightness(self, response):
        logger.info('handle brightness response')

    def handle_response(self, response):
        connection = response['connection']
        logger.debug("handle_response %s", str(response))
        connection.queue_task(response)
        # update config
        cmd = response['msg'][0]
        self.response_handlers[cmd](response)

        if response['status'] == 'OK':
            logger.debug('send notifications to all but %s', connection.name)
            response = copy.deepcopy(response)

            response['type'] = 'notify'
            for t in threading.enumerate():
                logger.debug('maybe notify %s', t.name)
                if t.name != connection.name and t.name.startswith('ConnectionThread-'):
                    logger.debug('NOTIFY %s', t.name)
                    t.queue_task(response)

            if cmd == 'shutdown':
                self.shutdown()
                    
    def handle_job(self, job):
        if not self.running:
            return

        logger.debug("handle_job %s", str(job))
        if job.has_key('type'):
            if job['type'] == 'request':
                self.handle_request(job)
            if job['type'] == 'response':
                self.handle_response(job)

    def run(self):
        self.running = True
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
            if not self.server.running:
                logger.info('server has stopped  running')
                self.stop()

        logger.info('no longer running')
        server.ClockServer.controller = None
        self.finished = True
