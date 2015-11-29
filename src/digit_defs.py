# Digit definitions
# Each digit is defined as an 8 bit bitmap.
# Bit 7 is segment A, bit 0 is the DP
# DIG_DP can be or'ed into a digit to turn it on

DIG_DP    = 0b00000001
DIG_SPACE = 0b00000000
DIG_0     = 0b11111100
DIG_1     = 0b01100000
DIG_2     = 0b11011010
DIG_3     = 0b11110010
DIG_4     = 0b01100110
DIG_5     = 0b10110110
DIG_6     = 0b10111110
DIG_7     = 0b11100000
DIG_8     = 0b11111110
DIG_9     = 0b11100110
DIG_A     = 0b11101110
DIG_b     = 0b00111110
DIG_C     = 0b10011100
DIG_c     = 0b00011010
DIG_d     = 0b01111010
DIG_E     = 0b10011110
DIG_F     = 0b10001110
# g
DIG_H     = 0b01101110
# i (?)
DIG_J     = 0b01110000
# k
DIG_L     = 0b00011100
# m
DIG_n     = 0b00101010
DIG_o     = 0b00111010
DIG_O     = DIG_0
DIG_P     = 0b11001110
# q
DIG_r     = 0b00001010
DIG_S     = DIG_5
DIG_t     = 0b00011110
DIG_U     = 0b01111100
DIG_u     = 0b00111000
# v
# w
# x
DIG_y     = 0b01110110
# z
