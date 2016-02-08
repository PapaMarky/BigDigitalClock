# Copyright 2016, Mark Dyer
import ClockControlThread
from threading import Thread
import logging

import RPi.GPIO as GPIO
import BigDisplay as B
from datetime import datetime as dt
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
            'mode': self.handle_mode
            }

        dsPin    = 16
        latchPin = 21
        clkPin   = 20
        pwmPin   = 18 # Broadcom pin 18 (P1 pin 12) Controls brightness of display

        self.display = B.BigDisplay('BigClock', dsPin, latchPin, clkPin, pwmPin)

        self._hour = -1
        self._min = -1
        self._sec = -1
        self.show_seconds = True

    def set_brightness(self, dc):
        self.display.set_brightness(dc)

    def displayColon(self):
        # TODO make this aware of settings
        self.display.set_colon(0, True)
        self.display.set_colon(1, True)
        self.display.set_colon(2, True)
    
    def splitDigits(self, d):
        if d > 99 or d < 0:
            return None
        hi = int(d / 10)
        lo = int(d - (hi * 10))
        #print "splitDigits({}): ({}, {})".format(d, lo, hi)
        return (lo, hi)

    def displayTime(self, now):
        self.displayColon()
        sec = self.splitDigits(now.second)
        min = self.splitDigits(now.minute)
        h = now.hour
        # TODO Make this aware of settings
        if h > 12:
            h = h - 12
        hr = self.splitDigits(h)

        self.display.set_digit(5, hr[1])
        self.display.set_digit(4, hr[0])

        self.display.set_digit(3, min[1])
        self.display.set_digit(2, min[0])

        self.display.set_digit(1, sec[1])
        self.display.set_digit(0, sec[0])


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
        if len(msg) != 2:
            request['status'] = 'BAD ARGS'
            return

        b = msg[1]
        logger.info('Setting clock brightness to %s', b)
        # TODO set brightness of hardware
        self.set_brightness(b)
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
        self.display.set_brightness(n)

    def handle_job(self, job):
        logger.debug('Handling Job: %s', str(job))

        if 'msg' in job and isinstance(job['msg'], list):
            cmd = job['msg'][0]
            logger.info('Calling handler for "%s"', cmd)
            self.request_handlers[cmd](job)

        # Queue up the results
        job['type'] = 'response'
        self.control_q.put(job)

    def run_display(self):
        # TODO settings
        now = dt.now()
        if self._hour != now.hour or self._min != now.minute or self._sec != now.second:
            self._hour = now.hour
            self._min = now.minute
            self._sec = now.second
            self.displayTime(now)
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
