#!/usr/bin/python
# Copyright 2016, Mark Dyer

from threading import Thread
import logging

logger = logging.getLogger('BigClock.ClockWorksThread')

class ClockWorksThread(Thread):
    def __init__(self, control_q, display_q):
        super(ClockWorksThread, self).__init__()
        self.control_q = control_q
        self.display_q = display_q

    def run(self):
        logger.info("ClockWorksThread Starting")
