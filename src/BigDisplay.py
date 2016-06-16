# copyright 2016, Mark Dyer
import shifter as S
import Tsl2591
import digit_defs as digits
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

        self.light_sensor = Tsl2591.Tsl2591()
        self.tsl_gain = 0
        self.tsl_timing = 3

        self.sensor_min = 0
        self.sensor_max = 1000
        self.pwm_min = 5
        self.pwm_max = 200

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
            
    def update(self):
        if self.auto_bright:
            self.update_auto_brightness()

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
        
    def set_brightness(self, dc):
        self.logger.info('Request Set Brightness: %s', dc)

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


