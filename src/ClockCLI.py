#!/usr/bin/python
import sys, os
import select
import ClockClient as c
import logging
import json

# Set up main logging stuff
id = "ClockCLI-{}".format(os.getpid())
logger = logging.getLogger(id)
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

    if type(msg) == 'str':
        msg = msg.split()

    if msg == 'shutdown':
        client.send_shutdown()

    if msg == '.':
        running = False
        return

    msg = msg.split()
    logger.info("Msg: %s", str(msg))
    if msg[0] == "brightness":
        client.set_brightness(int(msg[1]))
        return

def handle_message(msg):
    global running

    list = msg['msg']
    print ""
    type = msg['type'].upper()
    print "type: {}".format(type, str(msg['msg']))
    print "  STATUS: {}".format(msg['status'])

    if msg['msg'][0] == 'shutdown':
        running = False

if __name__ == '__main__':
    running = True
    id = "ClockCLI-{}".format(os.getpid())
    client = c.ClockClient(id)
    show_prompt()
    while running and client.running:
        line = check_for_input()
        while line is not None:
            handle_input(line)
            show_prompt()
            line = check_for_input()

        line = client.check_for_message()
        need_prompt = False

        while line is not None and line != '':
            need_prompt = True
            logger.info('got message: "%s"', line)
            msg = json.loads(line)
            handle_message(msg)
            line = client.check_for_message()

        if need_prompt:
            show_prompt()

    client.shutdown()
    print "Exiting"
