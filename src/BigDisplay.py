# copyright 2016, Mark Dyer
#import shifter as S

class BigDisplay:
    def __init__(self, ds, latch, clk):
#        self.shift = S.shifter(ds, latch, clk)
        self.digits = [' ',' ',' ',' ',' ',' ']
        self.decimals = [False, False, False, False, False, False]
        self.colons = [False, False, False];
        self.dirty = True

    def update_colons(self):
        colons = 0b00000000
        for i in range(3):
            if self.colons[i]:
                colons = colons | (0b00000001 << (8 - i))

        #print "COLONS: {:#010b}".format(colons)
        #self.shift.shiftout(colons)

    def update_digits(self):
        for i in range(6):
            
            
    def update(self):
        if self.dirty:
            self.dirty = False
            self.update_colons()
            self.update_digits()

    def set_colon(self, n, v):
        if self.colons[n] is not v:
            self.colons[n] = v
            self.dirty = True

    def set_digit(self, n, v):
        if self.digits[n] is not v:
            self.digits[n] = v
            self.dirty = True

    def set_decimal(self, n, v):
        if self.decimals[n] is not v:
            self.decimals[n] = v
            self.dirty = True


