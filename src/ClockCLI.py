#!/usr/bin/python

import ClockClient as c
import logging

# Set up main logging stuff
logger = logging.getLogger('ClockCLI')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/var/log/ClockCLI.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

if __name__ == '__main__':
    client = c.ClockClient('ClockCLI')

    running = True

    while running:
        msg = raw_input('ClockCLI>> ')
        logger.info("Command: '%s'", msg)

        if msg == 'shutdown':
            running = False

        if msg == '.':
            running = False
            break

        try:
            logger.info("Sending: '%s'", msg)
            client.send_message(msg)
        except:
            break
            

        if msg == 'done':
            running = False
            break

    client.shutdown()
