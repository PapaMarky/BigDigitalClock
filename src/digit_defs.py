# Digit definitions
# Each digit is defined as an 8 bit bitmap.
# Bit 7 is segment A, bit 0 is the DP
# DIG_DP can be or'ed into a digit to turn it on

DIG_DP    = 0b10000000
DIG_SPACE = 0b00000000
DIG_0     = 0b00111111
DIG_1     = 0b00000110
DIG_2     = 0b01011011
DIG_3     = 0b01001111
DIG_4     = 0b01100110
DIG_5     = 0b01101101
DIG_6     = 0b01111101
DIG_7     = 0b00000111
DIG_8     = 0b01111111
DIG_9     = 0b01100111
DIG_A     = 0b01110111
DIG_b     = 0b01111100
DIG_C     = 0b00111001
DIG_c     = 0b01011000
DIG_d     = 0b01011110
DIG_E     = 0b01111001
DIG_F     = 0b01110001
# g
DIG_H     = 0b01110110
# i (?)
DIG_J     = 0b00001110
# k
DIG_L     = 0b00111000
# m
DIG_n     = 0b01010100
DIG_o     = 0b01011100
DIG_O     = DIG_0
DIG_P     = 0b01110011
# q
DIG_r     = 0b01010000
DIG_S     = DIG_5
DIG_t     = 0b01111000
DIG_U     = 0b00111110
DIG_u     = 0b00011100
# v
# w
# x
DIG_y     = 0b01101110
# z
