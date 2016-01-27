#!/usr/bin/python
import sys
import shifter as S
from datetime import datetime as dt
import time
import digit_defs as d
import RPi.GPIO as GPIO
import BigDisplay as B

display = B.BigDisplay(16, 21, 20)

_hour = -1
_min = -1
_sec = -1

show_seconds = True

def displayColon():
    display.set_colon(0, show_seconds)
    display.set_colon(1, !show_seconds)
    display.set_colon(2, show_seconds)

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
    return (lo, hi)

def displayTime(now):
    displayColon()
    sec = splitDigits(now.second)
    min = splitDigits(now.minute)
    h = now.hour
    if h > 12:
        h = h - 12
    hr = splitDigits(h)

    display.set_digit(5, sec[1])
    display.set_digit(4, sec[0])

    display.set_digit(3, min[1])
    display.set_digit(2, min[0])

    display.set_digit(1, hr[1])
    display.set_digit(0, hr[0])

def cleanUp():
    display.clear_all()
    GPIO.cleanup()
    
try:
    while True:
        now = dt.now()
        if _hour != now.hour or _min != now.minute or _sec != now.second:
            _hour = now.hour
            _min = now.minute
            _sec = now.second
            displayTime(now)
            display.update()

        time.sleep(0.1)
except KeyboardInterrupt:
    cleanUp()
    sys.exit(0)

except Exception as inst:
    print "Exception: " + str(type(inst))
    print inst.args
    print inst
    cleanUp()

print "All Done."
cleanup()
