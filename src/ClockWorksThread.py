# Copyright 2016, Mark Dyer
import ClockControlThread
from threading import Thread
import logging

logger = logging.getLogger('BigClock.ClockWorksThread')

class ClockWorksThread(Thread):
    def __init__(self, control_q, display_q):
        super(ClockWorksThread, self).__init__(name='ClockWorks')
        self.control_q = control_q
        self.display_q = display_q
        self.running = True
        self.request_handlers = {
            'shutdown': self.handle_shutdown,
            'brightness': self.handle_brightness,
            'mode': self.handle_mode
            }

    def handle_shutdown(self, request):
        # TODO turn off the clock hardware
        request['status'] = 'OK'
        self.stop()

    def handle_brightness(self, request):
        msg = request['msg']
        if len(msg) != 2:
            request['status'] = 'BAD ARGS'
            return

        b = msg[1]
        logger.info('Setting clock brightness to %s', b)
        # TODO set brightness of hardware
        request['status'] = 'OK'

    def handle_mode(self, request):
        msg = request['msg']
        if len(msg) != 2:
            request['status'] = 'BAD ARGS'
            return
        m = msg[1]
        logger.info('Setting clock mode to "%s"', m)
        # TODO set mode of display controller
        request['status'] = 'OK'

    def stop(self):
        logger.info('stop() called')
        self.running = False

    def queue_task(self, task):
        self.display_q.put(task)

    def set_brightness(self, n):
        logger.info('set_brightness to %s', n)

    def handle_job(self, job):
        logger.debug('Handling Job: %s', str(job))

        if 'msg' in job and isinstance(job['msg'], list):
            cmd = job['msg'][0]
            logger.info('Calling handler for "%s"', cmd)
            self.request_handlers[cmd](job)

        # Queue up the results
        job['type'] = 'response'
        self.control_q.put(job)

    def run(self):
        logger.info("ClockWorksThread Starting")

        while self.running:
            while not self.display_q.empty():
                job = self.display_q.get()
                self.handle_job(job)
        
        logger.info("ClockWorksThread no longer running")
