# Copyright 2016, Mark Dyer

from threading import Thread
import logging

logger = logging.getLogger('BigClock.ClockWorksThread')

class ClockWorksThread(Thread):
    def __init__(self, control_q, display_q):
        super(ClockWorksThread, self).__init__()
        self.control_q = control_q
        self.display_q = display_q
        self.running = True

    def handle_job(self, job):
        logger.debug('Handling Job: %s', str(job))
        if job == 'shutdown':
            self.running = False
        
    def run(self):
        logger.info("ClockWorksThread Starting")

        while self.running:
            while not self.display_q.empty():
                job = self.display_q.get()
                self.handle_job(job)
        
