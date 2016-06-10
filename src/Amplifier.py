import smbus

TPA2016_I2CADDR = 0x58

TPA2016_SETUP    = 0x01
TPA2016_ATK      = 0x02
TPA2016_REL      = 0x03
TPA2016_HOLD     = 0x04
TPA2016_GAIN     = 0x05
TPA2016_AGCLIMIT = 0x06
TPA2016_AGC      = 0x07
TPA2016_AGC_OFF  = 0x00
TPA2016_AGC_2    = 0x01
TPA2016_AGC_4    = 0x02
TPA2016_AGC_8    = 0x03

TPA2016_SETUP_R_EN      = 0x80
TPA2016_SETUP_L_EN      = 0x40
TPA2016_SETUP_SWS       = 0x20
TPA2016_SETUP_R_FAULT   = 0x10
TPA2016_SETUP_L_FAULT   = 0x08
TPA2016_SETUP_THERMAL   = 0x04
TPA2016_SETUP_NOISEGATE = 0x01

class Amplifier(object):
    def __init__(self,
                 i2c_bus=1,
                 i2caddr=TPA2016_I2CADDR
                 ):
        self.bus = smbus.SMBus(i2c_bus)
        self.i2caddr = i2caddr
    
    def set_gain(self, g):
        if (g > 30):
            g = 30
        if (g < -28):
            g = -28
        self.write8(TPA2016_GAIN, g)

    def get_gain(self):
        g = self.read8(TPA2016_GAIN)
        print "GAIN: {}".format(g)
        
    def enable_channel(self, right, left):
        setup = self.read8(TPA2016_SETUP)
        if right:
            setup |= TPA2016_SETUP_R_EN
        else:
            setup &= ~TPA2016_SETUP_R_EN

        if left:
            setup |= TPA2016_SETUP_L_EN
        else:
            setup &= ~TPA2016_SETUP_L_EN

        self.write8(TPA2016_SETUP, setup)

    def set_agc_compression(self, x):
        if x > 3:
            return

        agc = read8(TPA2016_AGC)
        agc &= ~(0x03)
        agc |= x

        self.write8(TPA2016_AGC, agc)

    def set_release_control(self, release):
         # 0nly 6 bits
        if release > 0x3F:
            return

        self.write8(TPA2016_REL, release)


    def set_attack_control(self, attack):
         # 0nly 6 bits
        if attack > 0x3F:
            return

        self.write8(TPA2016_ATK, attack)


    def set_hold_control(self, hold):
         # 0nly 6 bits
        if hold > 0x3F:
            return

        self.write8(TPA2016_HOLD, hold)

    def set_limit_level_on(self):
        limit = self.read8(TPA2016_AGCLIMIT)
        print "LIMIT: {:02X}".format(limit)
        limit &= ~(0x80) # clear top bit
        print "LIMIT: {:02X}".format(limit)
        self.write8(TPA2016_AGCLIMIT, limit)

    def set_limit_level_off(self):
        limit = self.read8(TPA2016_AGCLIMIT)
        print "LIMIT: {:02X}".format(limit)
        limit |= 0x80 # set top bit
        print "LIMIT: {:02X}".format(limit)
        self.write8(TPA2016_AGCLIMIT, limit)

    def set_limit_level(self, l):
        if l > 31:
            return

        limit = self.read8(TPA2016_AGCLIMIT)
        print "LIMIT: {:02X}".format(limit)

        limit &= ~(0x1F) # clear bottom 5 bits
        limit |= l       # set limit level
        print "LIMIT: {:02X}".format(limit)
        self.write8(TPA2016_AGCLIMIT, limit)

    def get_limit_level(self):
        limit = self.read8(TPA2016_AGCLIMIT)
        print "LIMIT: {:02X}".format(limit)
        limit &= 0x1F
        print "LIMIT: {:02X}".format(limit)
        return limit

    
    def set_limit_level(self, limit):
        if limit > 31:
            return

        agc_limit = self.read8(TPA2016_AGCLIMIT)

        agc_limit &= ~(0x1F) # clear bottom 5 bits
        agc_limit != limit   # set level limit

        self.write8(TPA2016_AGCLIMIT, agc_limit)

    def set_agc_max_gain(self, x):
        if x > 12:
            return # max gain max is 12 (30dB)

        agc = self.read8(TPA2016_AGC)
        agc &= ~(0xF0)
        agc |= (x << 4)

        self.write8(TPA2016_AGC, agc)

    def read8(self, reg):
        return self.bus.read_byte_data(self.i2caddr, reg)

    def write8(self, reg, data):
        self.bus.write_byte_data(self.i2caddr, reg, data)
