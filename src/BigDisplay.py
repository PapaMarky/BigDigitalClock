# copyright 2016, Mark Dyer
import shifter as S
import digit_defs as digits
import logging
import pigpio

class BigDisplay:
    def __init__(self, log_name, ds, latch, clk, brightnessPin):
        self.logger = logging.getLogger('{}.Display'.format(log_name))
        self.logger.info('Creating Display')

        self.pi = pigpio.pi()

        self.shift = S.shifter('BigClock', ds, latch, clk)
        self.digits = [' ',' ',' ',' ',' ',' ']
        self.decimals = [False, False, False, False, False, False]
        self.colons = [False, False, False];
        self.dirty = True
        self.brightnessPin = brightnessPin
        self.pi.set_mode(brightnessPin, pigpio.ALT2)   # gpio 24 as ALT2
        self.pi.set_PWM_frequency(brightnessPin, 100)
        self.dc = 0 # start with LEDs turned off
        self.pi.set_PWM_dutycycle(brightnessPin, self.dc)
        

    def clear_all(self):
        for i in range(3):
            self.set_colon(i, False)
        for i in range(6):
            self.set_digit(i, ' ')
            self.set_decimal(i, False)

    def update_colons(self):
        colons = 0b00000000
        for i in range(3):
            if self.colons[i]:
                colons = colons | (0b00000001 << (8 - i))

        #print "COLONS: {:#010b}".format(colons)
        self.shift.shiftout(colons)

    def update_digits(self):
        for i in range(6):
            b = digits.get_bits(str(self.digits[i]))
            if self.decimals[i]:
                b = b | digits.DIG_DP

            #print "DIGIT[{}]: {} = {:#010b}".format(i, self.digits[i], b)
            self.shift.shiftout(b)
            
    def update(self):
        if self.dirty:
            self.dirty = False
            self.update_colons()
            self.update_digits()
            self.shift.latch()

    def set_brightness(self, dc):
        self.logger.info('Request Set Brightness: %s', dc)
        if dc > 255:
            dc = 255
        if dc < 0:
            dc = 0

        if self.dc != dc:
            self.logger.info('Set Brightness: %s', dc)
            self.dc = dc
            self.pi.set_PWM_dutycycle(self.brightnessPin, self.dc)

    def set_colon(self, n, v):
        if self.colons[n] is not v:
            self.colons[n] = v
            self.dirty = True

    def set_digit(self, n, v):
        #print "set_digit({}, {})".format(n, v)
        if self.digits[n] is not v:
            self.digits[n] = v
            self.dirty = True

    def set_decimal(self, n, v):
        if self.decimals[n] is not v:
            self.decimals[n] = v
            self.dirty = True


