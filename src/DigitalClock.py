#!/usr/bin/python
import sys
import shifter as S
from datetime import datetime as dt
import time
import digit_defs as d
import RPi.GPIO as GPIO
import BigDisplay as B
import logging

# Set up main logging stuff
logger = logging.getLogger('BigClock')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('/var/log/BigClock.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)


display = B.BigDisplay(16, 21, 20)

# brightness circuit test
import select
pwmPin = 18 # Broadcom pin 18 (P1 pin 12)
dc = 50     # duty cycle (0 - 100)

GPIO.setup(pwmPin, GPIO.OUT)
pwm = GPIO.PWM(pwmPin, 50)

_hour = -1
_min = -1
_sec = -1

show_seconds = True

def displayColon():
    display.set_colon(0, True)
    display.set_colon(1, True)
    display.set_colon(2, True)

def display2Digit(d):
    if d > 99 or d < 0:
        #ERROR
        return
    hi = int(d / 10)
    lo = int(d - (hi * 10))
#    print "d: " + str(d) + ", Hi: " + str(hi) + ", lo: " + str(lo)
    shifty.shiftout(digits[lo][0])
    shifty.shiftout(digits[hi][0])
    
def splitDigits(d):
    if d > 99 or d < 0:
        return None
    hi = int(d / 10)
    lo = int(d - (hi * 10))
    #print "splitDigits({}): ({}, {})".format(d, lo, hi)
    return (lo, hi)

def displayTime(now):
    displayColon()
    sec = splitDigits(now.second)
    min = splitDigits(now.minute)
    h = now.hour
    if h > 12:
        h = h - 12
    hr = splitDigits(h)

    display.set_digit(5, hr[1])
    display.set_digit(4, hr[0])

    display.set_digit(3, min[1])
    display.set_digit(2, min[0])

    display.set_digit(1, sec[1])
    display.set_digit(0, sec[0])


def cleanUp():
    display.clear_all()
    GPIO.cleanup()

# brightness circuit test
pwm.start(dc)

logger.info("Starting")
logger.info("Brightness: %d%%", dc)

try:
    while True:
        while False and sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().rstrip()
            print "LINE: '{}'".format(line)
            new_dc = dc
            if line.isdigit():
                new_dc = int(line)
            else:
                for c in line:
                    if c is '=' or c is '+':
                        new_dc = new_dc + 1
                    elif c is '-' or c is '_':
                        new_dc = new_dc - 1

            if new_dc > 100:
                new_dc = 100
            elif new_dc < 0:
                new_dc = 0

            if new_dc != dc:
                dc = new_dc
                print "DC: {}".format(dc)
                pwm.ChangeDutyCycle(dc)

        now = dt.now()
        if _hour != now.hour or _min != now.minute or _sec != now.second:
            _hour = now.hour
            _min = now.minute
            _sec = now.second
            displayTime(now)
            display.update()

        time.sleep(0.1)
except KeyboardInterrupt:
    logger.info("KeyboardInterrupt")
    cleanUp()
    sys.exit(0)

except Exception as inst:
    print "Exception: " + str(type(inst))
    print inst.args
    print inst
    logger.error("Exception: {}", str(type(inst)))
    logger.error(inst.args)
    logger.error(inst)
    cleanUp()

logger.info("All Done")
cleanUp()
