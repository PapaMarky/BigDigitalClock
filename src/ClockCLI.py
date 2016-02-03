#!/usr/bin/python
import sys, os
import select
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

global running
running = True

def check_for_input():
    try:
        if select.select([sys.stdin,], [], [], 0)[0]:
            return sys.stdin.readline().rstrip()
    except IOError:
        # this just means there was nothing to read
        pass

    return None

def show_prompt():
    sys.stdout.write('ClockCLI>> ')
    sys.stdout.flush()

def handle_input(msg):
    global running
    logger.info("Command: '%s'", msg)

    if msg == 'shutdown':
        running = False
        client.send_shutdown()

    if msg == '.':
        running = False
        return

    msg = msg.split(':')
    logger.info("Msg: %s", str(msg))
    if msg[0] == "brightness":
        client.set_brightness(int(msg[1]))
        return

    if msg == 'done':
        running = False
        return

if __name__ == '__main__':
    global running
    running = True
    id = "ClockCLI-{}".format(os.getpid())
    client = c.ClockClient(id)
    show_prompt()
    while running:
        line = check_for_input()
        while line is not None:
            handle_input(line)
            show_prompt()
            line = check_for_input()

        line = client.check_for_message()
        while line is not None:
            logging.info('got message: "%s"', line)
            print ""
            line = client.check_for_message()

    client.shutdown()
    print "Exiting"
