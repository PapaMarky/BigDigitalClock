#!/usr/bin/python
# Copyright 2016, Mark Dyer
import Queue
import ClockControlThread
import ClockWorksThread
import logging

# Set up main logging stuff
logger = logging.getLogger('BigClock')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/var/log/BigClock.log')
fh.setLevel(logging.DEBUG)
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
    clockworks_thread.daemon = True
    threads.append(clockworks_thread)
    clockworks_thread.start()

    clockcontrol_thread = ClockControlThread.ClockControlThread(control_q, display_q)
    clockcontrol_thread.daemon = True
    threads.append(clockcontrol_thread)
    clockcontrol_thread.start()

    for t in threads:
        t.join()

    logger.info("******** EXITING BigClockMain ********")



