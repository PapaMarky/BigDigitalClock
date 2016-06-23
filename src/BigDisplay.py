# copyright 2016, Mark Dyer
import shifter as S
import Tsl2591
import BME280

import digit_defs as digits
from ClockMessage import VALID_MODES

from datetime import datetime as dt
import time
import logging
import pigpio

class BigDisplay:
    def __init__(self, log_name, ds, latch, clk, brightnessPin, tsl_config):
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
        self.auto_bright = False

        self.mode_handlers = {
            'clock': {'update': self.update_clock_mode, 'start': None, 'stop': None},
            'off':   { 'update': self.update_off_mode, 'start': None, 'stop': None},
            'timetemp': {'update': self.update_timetemp_mode, 'start': None, 'stop': None}
            }

        # clock mode
        self._hour = -1
        self._min = -1
        self._sec = -1
        self.show_seconds = True

        self.light_sensor = Tsl2591.Tsl2591()
        self.tsl_gain = 0
        self.tsl_timing = 3

        self.sensor_min = 0
        self.sensor_max = 1000
        self.pwm_min = 5
        self.pwm_max = 200

        self.mode = 'clock'

        self.temp_sensor = BME280.BME280()
        self.temp_scale = 'F'
        self.timetemp_start = None
        self.timetemp_length = 5 # seconds
        self.timetemp_display = 'clock'

    def c_to_f(self, C):
        F = (C * 9)/5 + 32
        return F

    def config_autobright(self, config):
        self.sensor_min = config['sensor_min']
        self.sensor_max = config['sensor_max']
        self.pwm_min = config['pwm_min']
        self.pwm_max = config['pwm_max']

    def config_tsl(self, config):
        self.tsl_gain = config['gain']
        self.tsl_timing = config['timing']

        self.light_sensor.set_gain(self.tsl_gain)
        self.light_sensor.set_timing(self.tsl_timing)

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
                colons = colons | (0b00000001 << (7 - i))

        #print "COLONS: {:#010b}".format(colons)
        self.shift.shiftout(colons)

    def update_digits(self):
        for i in range(6):
            b = digits.get_bits(str(self.digits[i]))
            if self.decimals[i]:
                b = b | digits.DIG_DP

            #print "DIGIT[{}]: {} = {:#010b}".format(i, self.digits[i], b)
            self.shift.shiftout(b)

    def displayColon(self):
        # TODO make this aware of settings
        self.set_colon(0, True)
        self.set_colon(1, False)
        self.set_colon(2, True)
    
    def splitDigits(self, d):
        if d > 99 or d < 0:
            return None
        hi = int(d / 10)
        lo = int(d - (hi * 10))
        #print "splitDigits({}): ({}, {})".format(d, lo, hi)
        return (lo, hi)

    def set_temp_scale(self, scale):
        self.logger.debug('set_temp_scale: "%s"', scale)
        s = str(scale).upper()
        if s != 'C' and s != 'F':
            return False
        if s != self.temp_scale:
            self.temp_scale = s
            self.dirty = True
        return True

    def get_temp_scale(self):
        return self.temp_scale
        
    def displayTemp(self):
        temp  = self.temp_sensor.read_temperature() # celsius
        if self.temp_scale == 'F':
            temp = self.c_to_f(temp)
        temp_str = "{:3d}*{} ".format(int(round(temp)), self.temp_scale)
        #self.logger.debug('Current Temperature: "%s"', temp_str)

        # clear colon, set decimal point
        self.clear_all()

        self.set_digit(5, temp_str[0])
        self.set_digit(4, temp_str[1])
        self.set_digit(3, temp_str[2])
        self.set_digit(2, temp_str[3])
        self.set_digit(1, temp_str[4])
        self.set_digit(0, temp_str[5])

    def displayTime(self, now):
        sec = self.splitDigits(now.second)
        min = self.splitDigits(now.minute)
        h = now.hour
        # TODO Make this aware of settings
        if h > 12:
            h = h - 12
        hr = self.splitDigits(h)

        self.clear_all()
        self.displayColon()
        #logger.info('displayTime')

        self.set_digit(5, hr[1])
        self.set_digit(4, hr[0])

        self.set_digit(3, min[1])
        self.set_digit(2, min[0])

        self.set_digit(1, sec[1])
        self.set_digit(0, sec[0])

    def update_off_mode(self):
        pass

    def start_timetemp_mode(self):
        self.timetemp_start = time.time()

    def update_timetemp_mode(self):
        now = time.time()

        if self.timetemp_start == None:
            self.timetemp_start = time.time()

        elapsed = now - self.timetemp_start
        if elapsed >= self.timetemp_length:
            self.timetemp_start = self.timetemp_start + self.timetemp_length
            # switch display
            old_display = self.timetemp_display
            if self.timetemp_display == 'clock':
                self.timetemp_display = 'temp'
            else:
                self.timetemp_display = 'clock'

            # self.logger.debug('switch timetemp display from "%s" to "%s"', old_display, self.timetemp_display)

        if self.timetemp_display == 'clock':
            self.update_clock_mode()
        else:
            self.displayTemp()

    def update_clock_mode(self):
        now = dt.now()
        if self._hour != now.hour or self._min != now.minute or self._sec != now.second:
            self._hour = now.hour
            self._min = now.minute
            self._sec = now.second
            self.displayTime(now)
        
    def update(self):
        if self.auto_bright:
            self.update_auto_brightness()

        if self.mode in self.mode_handlers:
            self.mode_handlers[self.mode]['update']()

        if self.dirty:
            self.shift.unlatch()
            self.dirty = False
            self.update_colons()
            self.update_digits()
            self.shift.latch()
        
    def update_brightness(self, dc):
        if dc > 255:
            self.logger.info('Clamped brightness to 255')
            dc = 255
        if dc < 0:
            self.logger.info('Clamped brightness to 0')
            dc = 0

        if self.dc != dc:
            self.logger.info('Set Brightness: %s', dc)
            self.dc = dc
            self.pi.set_PWM_dutycycle(self.brightnessPin, self.dc)
        return dc

    def get_brightness(self):
        b = self.dc
        if self.auto_bright:
            b = 'auto'
        return b

    def set_brightness(self, dc):
        self.logger.info('Request Set Brightness: %s (%s)', dc, type(dc))

        if isinstance(dc, int):
            self.auto_bright = False
            self.update_brightness(dc)

        if dc == 'auto':
            self.auto_bright = True
            return dc

        return self.dc

    def map_luminosity_to_pwm(self, lum):
        # (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        return (lum - self.sensor_min) * (self.pwm_max - self.pwm_min) / (self.sensor_max - self.sensor_min) + self.pwm_min

    def update_auto_brightness(self):
        # read the sensor
        full, ir = self.light_sensor.get_full_luminosity()
        pwm = self.map_luminosity_to_pwm(full)
        # set the PWM
        self.update_brightness(pwm)

    def get_mode(self):
        return self.mode

    def set_mode(self, m):
        self.logger.info('Request Set Mode: "%s"', m)
        old_mode = self.mode
        if m in VALID_MODES:
            if old_mode and self.mode_handlers[old_mode]['stop'] is not None:
                self.mode_handlers[old_mode]['stop']()
            if self.mode_handlers[m]['start'] is not None:
                self.mode_handlers[m]['start']()
            self.mode = m

        return self.mode

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


