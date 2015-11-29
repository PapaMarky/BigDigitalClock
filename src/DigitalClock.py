import shifter as S
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

try:
    while True:
        # for seg in segments:
        #     shifty.shiftout(seg[1])
        #     raw_input(seg[0] + '...')
        i = 0
        for digit in digits:
            print digit[1]
            dp = 0
            if i % 2:
                dp = segments[7][1]
            i = i + 1
            shifty.shiftout(digit[0] | dp)
            shifty.shiftout(digit[0] | dp)

            shifty.shiftout(digit[0] | dp)
            shifty.shiftout(digit[0] | dp)

            shifty.shiftout(digit[0] | dp)
            shifty.shiftout(digit[0] | dp)

            shifty.latch()
            time.sleep(1)
except:
    shifty.shiftout(0)
    shifty.shiftout(0)

    shifty.shiftout(0)
    shifty.shiftout(0)

    shifty.shiftout(0)
    shifty.shiftout(0)

    shifty.latch()

print "All Done."
GPIO.cleanup()
