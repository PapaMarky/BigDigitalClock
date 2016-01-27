# copyright 2016, Mark Dyer

import threading
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

class ClockControlThread(threading.Thread):

    def run(self):
        logging.debug('running')
        return

