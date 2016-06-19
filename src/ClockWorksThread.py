# Copyright 2016, Mark Dyer
import ClockControlThread
from ClockMessage import VALID_MODES

from threading import Thread
import logging

import RPi.GPIO as GPIO
import BigDisplay as B
import time


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
            'mode': self.handle_mode,
            'initialize': self.handle_initialize,
            'config-light-sensor': self.handle_config_light_sensor,
            }

        logger.info('create display object')
        dsPin    = 16
        latchPin = 21
        clkPin   = 20
        pwmPin   = 19
        tsl_config = None
        self.display = B.BigDisplay('BigClock', dsPin, latchPin, clkPin, pwmPin, tsl_config)

    def cleanup(self):
        self.display.clear_all()
        GPIO.cleanup()

    def handle_shutdown(self, request):
        # TODO turn off the clock hardware
        self.set_brightness(0)
        request['status'] = 'OK'
        self.stop()

    def handle_brightness(self, request):
        msg = request['msg']
        if len(msg) > 2:
            request['status'] = 'BAD ARGS'
            return

        b = 'get'
        if len(msg) > 1:
            b = msg[1]
        logger.info('Setting clock brightness to %s', b)

        b = self.set_brightness(b)
        if len(msg) > 1:
            msg[1] = b
        else:
            msg.append(b)
        request['status'] = 'OK'

    def handle_initialize(self, request):
        logger.info('Initialization request: "%s"', request)
        # 2016-06-13 10:03:42,149 - INFO - BigClock.ClockWorksThread - Initialization request: "{'msg': ['initialize', {'brightness': 50}], 'source': 'ControlThread', 'connection': <ClockControlThread(ControlThread, started -1250020240)>, 'internal': True, 'type': 'request'}"
        msg = request['msg']
        settings = msg[1]
        if 'autobright' in settings:
            ab = settings['autobright']
            self.display.config_autobright(ab)
        else:
            logging.warn('"autobright" missing from initialization')

        if 'lightsensor' in settings:
            ls = settings['lightsensor']
            self.display.config_tsl(ls)
        else:
            logging.warn('"lightsensor" missing from initialization')
            
        if 'brightness' in settings:
            b = settings['brightness']
            self.set_brightness(b)
        else:
            logging.warn('"brightness" missing from initialization')

        request['status'] = 'OK'
        
    def handle_mode(self, request):
        msg = request['msg']
        if len(msg) > 2:
            request['status'] = 'BAD ARGS'
            return

        m = self.display.get_mode()
        s = 'OK'
        if len(msg) > 1:
            m = msg[1]
            if m not in VALID_MODES:
                s = 'BAD ARGS'
            m = self.display.set_mode(m)

        logger.info('Setting clock mode to "%s"', m)
        if len(msg) > 1:
            msg[1] = m
        else:
            msg.append(m)

        request['status'] = s

    def handle_config_light_sensor(self, request):
        # share code with initialization
        msg = request['msg']
        
    def stop(self):
        logger.info('stop() called')
        self.running = False

    def queue_task(self, task):
        self.display_q.put(task)

    def set_brightness(self, n):
        logger.info('set_brightness to %s', n)
        return self.display.set_brightness(n)

    def handle_job(self, job):
        logger.debug('Handling Job: %s', str(job))

        if 'msg' in job and isinstance(job['msg'], list):
            cmd = job['msg'][0]
            if cmd in self.request_handlers:
                logger.info('Calling handler for "%s"', cmd)
                self.request_handlers[cmd](job)
            else:
                logger.error('No handler for "%s"', cmd)
                job['status'] = 'NO HANDLER'

        # Queue up the results
        job['type'] = 'response'
        self.control_q.put(job)

    def run_display(self):
        # TODO settings
        self.display.update()

    def run(self):
        logger.info("ClockWorksThread Starting")
        self.set_brightness(50)

        while self.running:
            while not self.display_q.empty():
                job = self.display_q.get()
                self.handle_job(job)
            self.run_display()

        self.cleanup()
        logger.info("ClockWorksThread no longer running")
