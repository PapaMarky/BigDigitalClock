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

    def stop(self):
        logger.info('stop() called')
        self.running = False

    def queue_task(self, task):
        self.display_q.put(task)

    def set_brightness(self, n):
        logger.info('set_brightness to %s', n)

    def handle_job(self, job):
        logger.debug('Handling Job: %s', str(job))
        if job['msg'][0] == 'shutdown':
            self.stop()
            job['status'] = 'OK'

        if job['msg'][0] == 'brightness':
            self.set_brightness(job['msg'][1])
            job['status'] = 'OK'

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
