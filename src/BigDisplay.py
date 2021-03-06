# copyright 2016, Mark Dyer
import shifter as S
import Tsl2591
#import BME280
from bme280 import bme280
from bme280 import bme280_i2c

bme280_i2c.set_default_i2c_address(0x77)
bme280_i2c.set_default_bus(1)
bme280.setup()

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
            }

        # clock configs
        self.clock_zero_pad_hour = True
        self.clock_show_seconds = True
        self.clock_show_temp = False

        # clock mode
        self._hour = -1
        self._min = -1
        self._sec = -1

        self.light_sensor = None
        self.tsl_gain = 0
        self.tsl_timing = 3

        self.sensor_min = 0
        self.sensor_max = 1000
        self.pwm_min = 5
        self.pwm_max = 200

        self.mode = 'clock'

        self.temp_scale = 'F'
        self.timetemp_start = None
        self.timetemp_length = 5 # seconds
        self.timetemp_display = 'clock'

    def get_light_sensor(self):
        if self.light_sensor is None:
            try:
                self.light_sensor = Tsl2591.Tsl2591()
            except IOError, e:
                self.logger.exception('IOError creating light_sensor')
                if self.light_sensor is not None:
                    self.logger.warn('light_sensor not None: "%s"', str(self.light_sensor))
                    self.light_sensor = None
            except Exception, e:
                self.logger.exception('Exception creating light_sensor (%s)', str(e))
                if self.light_sensor is not None:
                    self.logger.warn('light_sensor not None: "%s"', str(self.light_sensor))
                    self.light_sensor = None
        return self.light_sensor
                
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

        light_sensor = self.get_light_sensor()
        if light_sensor is not None:
            light_sensor.set_gain(self.tsl_gain)
            light_sensor.set_timing(self.tsl_timing)

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
        if self.clock_show_seconds:
            self.set_colon(0, True)
            self.set_colon(1, False)
            self.set_colon(2, True)
        else:
            self.set_colon(0, False)
            self.set_colon(1, True)
            self.set_colon(2, False)
    
    def splitDigits(self, d):
        if d > 99 or d < 0:
            return None
        hi = int(d / 10)
        lo = int(d - (hi * 10))
        #print "splitDigits({}): ({}, {})".format(d, lo, hi)
        return [lo, hi]

    def set_clock_zero_pad_hour(self, v):
        self.logger.debug('set_clock_zero_pad_hour: "%s"', v)
        if isinstance(v, bool):
            self.clock_zero_pad_hour = v
        return self.clock_zero_pad_hour

    def get_clock_zero_pad_hour(self):
        return self.clock_zero_pad_hour

    def set_clock_show_seconds(self, v):
        self.logger.debug('set_clock_show_seconds(%d)', v)
        if isinstance(v, bool):
            self.clock_show_seconds = v
        return self.clock_show_seconds

    def get_clock_show_seconds(self):
        return self.clock_show_seconds

    def set_clock_show_temp(self, v):
        self.logger.debug('set_clock_show_temp(%d)', v)
        self.start_timetemp_mode()
        if isinstance(v, bool):
            self.clock_show_temp = v
        return self.clock_show_temp

    def get_clock_show_temp(self):
        return self.clock_show_temp

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
        data = bme280.read_all()
        temp = data.temperature

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

    def displayTime(self):
        now = dt.now()

        if self._hour != now.hour or self._min != now.minute or (self.clock_show_seconds and self._sec != now.second):
            self._hour = now.hour
            self._min = now.minute
            self._sec = now.second
        else:
            return

        sec = self.splitDigits(now.second)
        minute = self.splitDigits(now.minute)
        h = now.hour
        # TODO Make this aware of settings
        if h > 12:
            h = h - 12
        hr = self.splitDigits(h)

        #self.logger.debug('hr[0] = "%s", hr[1] = "%s"', hr[0], hr[1])
        if hr[1] == 0 and not self.clock_zero_pad_hour:
            hr[1] = ' '
        #self.logger.debug('hr[0] = "%s", hr[1] = "%s"', hr[0], hr[1])

        self.clear_all()
        self.displayColon()
        #logger.info('displayTime')

        if self.clock_show_seconds:
            self.set_digit(5, hr[1])
            self.set_digit(4, hr[0])

            self.set_digit(3, minute[1])
            self.set_digit(2, minute[0])

            self.set_digit(1, sec[1])
            self.set_digit(0, sec[0])
        else:
            self.set_digit(5, ' ')

            self.set_digit(4, hr[1])
            self.set_digit(3, hr[0])
            
            self.set_digit(2, minute[1])
            self.set_digit(1, minute[0])

            self.set_digit(0, ' ')

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
                # The clock only refreshes the time if the time has changed. When not show_seconds is False,
                # seconds are ignored in this comparison. When we are displaying time and tempurature but
                # not showing seconds, we display the temperature as expected, but when returning to time 
                # display, if the hour and minute have not changed, the display is not updated and continues
                # to display the temperature. 
                # By setting the remembered hour to -1, we trick the display into updating to show the time.
                self._hour = -1
                self.timetemp_display = 'clock'

            # self.logger.debug('switch timetemp display from "%s" to "%s"', old_display, self.timetemp_display)

        if self.timetemp_display == 'clock':
            self.displayTime()
        else:
            self.displayTemp()

    def update_clock_mode(self):
        if self.clock_show_temp:
            self.update_timetemp_mode()
            return

        self.displayTime()
        
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
        sensor = self.get_light_sensor()
        if sensor is None:
            # self.logger.debug('Sensor is NONE')
            return
        try:
            full, ir = sensor.get_full_luminosity()
        except Exception, e:
            self.logger.exception('Exception reading light sensor (%s)', str(e))
            return

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


