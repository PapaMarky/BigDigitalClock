#!/usr/bin/python
import sys
import shifter as S
from datetime import datetime as dt
import time
import digit_defs as d
import RPi.GPIO as GPIO

shifty = S.shifter(16, 21, 20)

digits = [(d.DIG_0, 0), (d.DIG_1, 1), (d.DIG_2, 2), (d.DIG_3, 3), (d.DIG_4, 4), (d.DIG_5, 5),
          (d.DIG_6, 6), (d.DIG_7, 7), (d.DIG_8, 8), (d.DIG_9, 9) ]

segments = [
    ('A',  0b10000000),
    ('B',  0b01000000),
    ('C',  0b00100000),
    ('D',  0b00010000),
    ('E',  0b00001000),
    ('F',  0b00000100),
    ('G',  0b00000010),
    ('DP', 0b00000001)
    ]

_hour = -1
_min = -1
_sec = -1

def display2Digit(d):
    if d > 99 or d < 0:
        #ERROR
        return
    hi = int(d / 10)
    lo = int(d - (hi * 10))
#    print "d: " + str(d) + ", Hi: " + str(hi) + ", lo: " + str(lo)
    shifty.shiftout(digits[lo][0])
    shifty.shiftout(digits[hi][0])
    
def displayTime(now):
    display2Digit(now.second)
    display2Digit(now.minute)
    h = now.hour
    if h > 12:
        h = h - 12
    display2Digit(h)
    shifty.latch()

def cleanUp():
    shifty.shiftout(0)
    shifty.shiftout(0)

    shifty.shiftout(0)
    shifty.shiftout(0)

    shifty.shiftout(0)
    shifty.shiftout(0)

    shifty.latch()
    GPIO.cleanup()
    
try:
    while True:
        now = dt.now()
        if _hour != now.hour or _min != now.minute or _sec != now.second:
            _hour = now.hour
            _min = now.minute
            _sec = now.second
            displayTime(now)

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
GPIO.cleanup()
