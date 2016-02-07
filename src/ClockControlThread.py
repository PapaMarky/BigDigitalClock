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
        logger.info('shutdown - shutting down server')
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

    def resp_shutdown(self, response):
        logger.info('handle shutdown response')

    def resp_mode(self, response):
        logger.info('handle mode response')

    def resp_brightness(self, response):
        logger.info('handle brightness response')
        # update the config file
        tokens = response['msg']
        b = tokens[1]
        self.config.set_brightness(b)
        

    def handle_response(self, response):
        connection = response['connection']
        logger.debug("handle_response %s", str(response))
        # put the response in the queue of the connection the request came in on
        connection.queue_task(response)

        # call the appropriate response handler to do any post processing.
        # update config, etc
        cmd = response['msg'][0]
        self.response_handlers[cmd](response)

        # if the response indicates that the request succeeded, notify all
        # other connections so they can update their view of the world.
        # TODO: move this to a function and call it from the response handlers
        # for requests that need to send notifications
        if response['status'] == 'OK':
            logger.debug('send notifications to all but %s', connection.name)
            # make a copy so that we are not modifying the object in the task_q of the
            # connection that recieved the request. We change 'type' from 'response'
            # to 'notify' so clients can tell if they sent the request or not.
            response = copy.deepcopy(response)

            response['type'] = 'notify'
            for t in threading.enumerate():
                if t.name != connection.name and t.name.startswith('ConnectionThread-'):
                    logger.debug('NOTIFY %s', t.name)
                    t.queue_task(response)

            if cmd == 'shutdown':
                self.shutdown()

    def handle_job(self, job):
        if not self.running:
            return

        logger.debug("handle_job %s", str(job))
        # TODO: create new type 'control' and use it, for example, to shutdown thread
        if job.has_key('type'):
            if job['type'] == 'request':
                self.handle_request(job)
            if job['type'] == 'response':
                self.handle_response(job)

    def run(self):
        self.running = True
        config_file = '/var/BigClock/config.json'

        logger.info("ClockControlThread Starting")
        self.config = config.ClockConfig(config_file)

        if self.config is None:
            logger.error("Failed to load configuration: '%s'", config_file)
            return

        HOST, PORT = 'localhost', 60969

        logger.info("ClockControlThread Starting Server")
        try:
            self.server = server.ClockServer(self, HOST, PORT)
            self.server.start()
        except Exception, e:
            logger.error("Failed to start server thread")
            return

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
