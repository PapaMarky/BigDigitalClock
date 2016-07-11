# Copyright 2016, Mark Dyer
import threading
import json

import ClockConfig as config
import ClockServer as server
from ClockMessage import create_request
from ClockMessage import VALID_COMMANDS
from ClockMessage import VALID_CONFIGS

import logging
import copy

logger = logging.getLogger('BigClock.ControlThread')

class ClockControlThread(threading.Thread):
    def __init__(self, control_q, display_q):
        super(ClockControlThread, self).__init__(name='ControlThread')
        self.control_q = control_q
        self.display_q = display_q
        self.running = True
        self.finished = False
        self.response_handlers = {
            'shutdown':   self.resp_shutdown,
            'get':        self.resp_get,
            'set':        self.resp_set
            }

    def stop(self):
        logger.info('stop() called')
        self.running = False

    def queue_task(self, task):
        self.control_q.put(task)

    def shutdown(self):
        logger.info('shutdown - shutting down server')
        self.server.stop()
        self.stop()

    def handle_get_request(self, request):
        logger.debug('*** handle_get_request(%s)', str(request))
        connection = request['connection']
        request['type'] = 'response'
        if 'msg' in request:
           msg = request['msg']
           if len(msg) < 2:
               request['status'] = 'BAD ARGS'
           else:
               config = msg[1]
               logger.debug('    Getting "%s"', config)
               if config in VALID_CONFIGS:
                   request['status'] = 'OK'
                   if config == 'brightness':
                       b = self.config.get_brightness()
                       logger.debug('   *** brightness: %s', b)
                       request['value'] = json.dumps({'brightness': b})
                   elif config == 'mode':
                       request['status'] = 'OK'
                       m = self.config.get_mode()
                       logger.debug('   *** mode: %s', m)
                       request['value'] = {'mode': m}
                   elif config == 'temp':
                       if len(msg) < 3:
                           request['status'] = 'MISSING TEMP CONFIG'
                       else:
                           subconfig = msg[2]
                           if subconfig == 'scale':
                               s = self.config.get_temp_scale()
                               logger.debug('   *** temp scale: %s', s)
                               request['value']  = {'temp': {'scale': s}}
                               request['status'] = 'OK'
                           else:
                               request['status'] = 'UNIMPLEMENTED TEMP CONFIG'
                   elif config == 'clock':
                       subconfig = msg[2]
                       if subconfig == 'zero_pad_hour':
                           z = self.config.get_clock_zero_pad_hour()
                           logger.debug('  *** clock zero_pad_hour: %s', z)
                           request['value'] = {'clock': {'zero_pad_hour': z}}
                           request['status'] = 'OK'
                       else:
                           request['status'] = 'UNIMPLEMENTED CLOCK CONFIG'
                   else:
                       request['status'] = 'UNIMPLEMENTED CONFIG'
               else:
                   request['status'] = 'BAD CONFIG'
        else:
            request['status'] = 'BROKEN'

        connection.queue_task(request)

    def handle_request(self, request):
        sender_name = ''
        if not 'internal' in request:
            sender_name = request['connection'].thread.name
        else:
            sender_name = 'CONTROL'

        # validate non-ConnectionThread 'connection'
        logger.info("Message From '%s': '%s'", sender_name, str(request))
        tokens = request['msg']
        if tokens[0] == 'get':
            self.handle_get_request(request)
            return
        elif tokens[0] in VALID_COMMANDS or sender_name == 'CONTROL':
            self.display_q.put(request)
        else:
            logger.error("bad request: '%s'", tokens[0])
            connection = request['connection']
            request['type'] = 'response'
            request['status'] = 'BAD REQUEST'
            connection.queue_task(request)

    def resp_shutdown(self, response):
        logger.info('handle shutdown response')

    def resp_get(self, response):
        logger.info('THIS SHOULD NEVER HAPPEN: handle "get" response: %s', str(response))
        tokens = response['msg']
        if len(tokens) < 2:
            response['status'] = 'BAD ARGS'
            return
        config = tokens[1]
        logger.info(' -- getting "%s"', config)

    def resp_set(self, response):
        logger.info('handle set response: %s', str(response))
        if response['status'] != 'OK':
            logger.info(' -- command failed: %s', response['status'])
            return

        if 'value' in response:
            v = response['value']
            logger.info('VALUE: %s', str(v))
            for config in v:
                logger.info(' -- config: %s', config)
                if config == 'brightness':
                    self.config.set_brightness(v[config])
                elif config == 'mode':
                    self.config.set_mode(v[config])
                elif config == 'temp':
                    for subconfig in v[config]:
                        logger.info(' -- subconfig: "%s"', subconfig)
                        if subconfig == 'scale':
                            logger.info('    -- value: %s', v[config][subconfig])
                            self.config.set_temp_scale(v[config][subconfig])
                        else:
                            response['status'] = 'BAD RESPONSE'
                else:
                    response['status'] = 'BAD RESPONSE'
        else:
            response['status'] = 'MISSING VALUE'

    def resp_bad_cmd(self, response):
        logger.info('handle bad response: %s', str(response))
        response['status'] = 'BAD CMD'

    def handle_response(self, response):
        connection = response['connection']
        logger.debug("handle_response %s", str(response))
        if 'internal' in response:
            logger.debug('Internal Message. The buck stops here')
            return
        # put the response in the queue of the connection the request came in on
        connection.queue_task(response)

        # call the appropriate response handler to do any post processing.
        # update config, etc
        cmd = response['msg'][0]
        if cmd in self.response_handlers:
            self.response_handlers[cmd](response)
        else:
            self.resp_bad_cmd(response)

        # if the response indicates that the request succeeded, notify all
        # other connections so they can update their view of the world.
        # TODO: move this to a function and call it from the response handlers
        # for requests that need to send notifications
        if response['status'] == 'OK':
            logger.debug('send notifications to all but %s', connection.name)
            # make a copy so that we are not modifying the object in the task_q of the
            # connection that recieved the request. We change 'type' from 'response'
            # to 'notify' so clients can tell if they sent the request or not.
            try:
                response = copy.deepcopy(response)
            except Exception, e:
                logger.error('Deepcopy Exception: %s', e)

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
            elif job['type'] == 'response':
                self.handle_response(job)

    def initial_settings(self):
        ls = self.config.get_lightsensor()
        ab = self.config.get_autobright()
        b = self.config.get_brightness()
        m = self.config.get_mode()
        temp_scale = self.config.get_temp_scale()
        zero_pad = self.config.get_clock_zero_pad_hour()

        logger.debug('initial_settings: my name: "%s"', self.name)
        message = create_request(self.name, ['initialize', {'brightness': b, 'autobright': ab, 'lightsensor': ls, 'mode': m, 'temp': {'scale': temp_scale}, 'clock':{'zero_pad_hour': zero_pad}} ] )
        message['internal'] = True
        message['connection'] = self
        self.handle_request(message)

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

        # send newly loaded config settings downstream
        self.initial_settings()

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
