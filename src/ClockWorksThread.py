# Copyright 2016, Mark Dyer
import ClockControlThread
from ClockMessage import VALID_MODES
from ClockMessage import VALID_CLOCK_CONFIGS
from ClockMessage import str_to_bool

from threading import Thread
import logging
import json

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
            'initialize': self.handle_initialize,
            'config-light-sensor': self.handle_config_light_sensor,
            'set': self.handle_set,
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
        self.display.set_brightness(0)
        request['status'] = 'OK'
        self.stop()

    def handle_set(self, request):
        logger.info('set request: "%s"', request)
        msg = request['msg']
        if len(msg) < 3:
            request['status'] = 'BAD ARGS'
            return

        config = msg[1]
        value = msg[2]

        request['status'] = 'OK'
        
        if config == 'brightness':
            if value != 'auto':
                try:
                    value = int(value)
                except ValueError,e:
                    request['status'] = 'BAD BRIGHTNESS'
                    request['value'] = {config: self.display.get_brightness()}
                    return

            value = self.display.set_brightness(value)
            request['value'] = {config: value}
        elif config == 'mode':
            v = self.display.set_mode(value)
            if v != value:
                request['status'] = 'BAD MODE'
            
            request['value'] = {config: v}
        elif config == 'temp':
            if len(msg) != 4:
                request['status'] = 'BAD TEMP ARGS'
                return
            tconfig = msg[2]
            tvalue = msg[3]
            if tconfig == 'scale':
                tvalue = tvalue.upper()
                if tvalue != 'C' and tvalue != 'F':
                    request['status'] = 'BAD TEMP SCALE'
                else:
                    if not self.display.set_temp_scale(tvalue):
                        request['status'] = 'FAILED'
                request['value'] = {'temp': {'scale': self.display.get_temp_scale()}}
            else:
                request['status'] = 'UNKNOWN TEMP CONFIG'
        elif config == 'clock':
            if len(msg) != 4:
                request['status'] = 'BAD CLOCK ARGS'
                return
            cconfig = msg[2]
            cvalue = msg[3]
            if cconfig not in VALID_CLOCK_CONFIGS:
                request['status'] = 'UNKNOWN CLOCK CONFIG'
                return
            if cconfig == 'zero_pad_hour':
                try:
                    cvalue = str_to_bool(cvalue)
                except Exception, e:
                    logging.exception('Non-bool zero_pad_hour: %s', cvalue)
                    cvalue = None
                if cvalue is None:
                    request['status'] = 'BAD TYPE'
                    return
                v = self.display.set_clock_zero_pad_hour(cvalue)
                request['value'] = {'clock': {'zero_pad_hour': v}}
            elif cconfig == 'show_seconds':
                try:
                    cvalue = str_to_bool(cvalue)
                except Exception, e:
                    logging.exception('Non-bool show_seconds: %s', cvalue)
                    cvalue = None
                if cvalue is None:
                    request['status'] = 'BAD TYPE'
                    return
                v = self.display.set_clock_show_seconds(cvalue)
                request['value'] = {'clock': {'show_seconds': v}}
                
            else:
                request['status'] = 'UNIMPLEMENTED CLOCK CONFIG'
        else:
            request['status'] = 'UNKNOWN CONFIG'
            request['value'] = value
            
    def handle_initialize(self, request):
        logger.info('Initialization request: "%s"', request)
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
            self.display.set_brightness(b)
        else:
            logging.warn('"brightness" missing from initialization')

        if 'mode' in settings:
            m = settings['mode']
            self.display.set_mode(m)

        if 'temp' in settings:
            t = settings['temp']
            logging.info('initialize temp: %s', str(t))
            if 'scale' in t:
                logging.info('initialize temp scale: %s', t['scale'])
                self.display.set_temp_scale(t['scale'])

        if 'clock' in settings:
            c = settings['clock']
            logging.info('initialize clock: %s', str(c))

            if 'zero_pad_hour' in c:
                logging.info(' - zero_pad_hour: %s', str(c['zero_pad_hour']))
                self.display.set_clock_zero_pad_hour(c['zero_pad_hour'])
            else:
                logging.warn('"clock zero_pad_hour" missing from initialization')

            if 'show_seconds' in c:
                logging.info(' - show_seconds: %s', str(c['show_seconds']))
                self.display.set_clock_show_seconds(c['show_seconds'])
            else:
                logging.warn('"clock show_seconds" missing from initialization')

        request['status'] = 'OK'

    def handle_config_light_sensor(self, request):
        # share code with initialization
        msg = request['msg']
        
    def stop(self):
        logger.info('stop() called')
        self.running = False

    def queue_task(self, task):
        self.display_q.put(task)

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
        self.display.set_brightness(50)

        while self.running:
            while not self.display_q.empty():
                job = self.display_q.get()
                self.handle_job(job)
            self.run_display()

        self.cleanup()
        logger.info("ClockWorksThread no longer running")
