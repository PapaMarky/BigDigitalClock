#!/usr/bin/python
# Copyright 2016, Mark Dyer
import Queue
import ClockControlThread
import ClockWorksThread
import logging
import sys
import time
import threading

# Set up main logging stuff
logger = logging.getLogger('BigClock')
logger.setLevel(logging.ERROR)
fh = logging.FileHandler('/var/log/BigClock.log')
fh.setLevel(logging.ERROR)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

if __name__ == "__main__":
    logger.info("******** START BigClockMain ********")

    logger.debug("Set up Job Queues")
    control_q = Queue.Queue()
    display_q = Queue.Queue()

    logger.debug("Starting Threads")
    threads = []
    # Start the threads
    clockworks_thread = ClockWorksThread.ClockWorksThread(control_q, display_q)
    #clockworks_thread.daemon = True
    threads.append(clockworks_thread)
    clockworks_thread.start()

    clockcontrol_thread = ClockControlThread.ClockControlThread(control_q, display_q)
    #clockcontrol_thread.daemon = True
    threads.append(clockcontrol_thread)
    clockcontrol_thread.start()

    while clockcontrol_thread.running or clockworks_thread.running:
        pass

    while clockworks_thread.running:
        logger.info('Main shutting down clockworks_thread')
        clockworks_thread.stop()
        time.sleep(2)

    while clockcontrol_thread.running:
        logger.info('Main shutting down clockcontrol_thread')
        clockcontrol_thread.stop()
        time.sleep(2)

    logger.info("******** EXITING BigClockMain ********")

    for t in threading.enumerate():
        logger.info('leftover: %s', t.name)



