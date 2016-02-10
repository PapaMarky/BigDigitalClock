import RPi.GPIO as GPIO
import time
import logging

#GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)

class shifter:
  def __init__(self, logger_name, ds, latch, clk):
    self.logger = logging.getLogger('{}.Shifter'.format(logger_name))
    self.PIN_DATA  = ds # 16
    self. PIN_LATCH = latch # 21
    self.PIN_CLOCK = clk # 20

    GPIO.setup(self.PIN_DATA,  GPIO.OUT)
    GPIO.setup(self.PIN_LATCH, GPIO.OUT)
    GPIO.setup(self.PIN_CLOCK, GPIO.OUT)

  def shiftout(self, byte):
    GPIO.output(self.PIN_LATCH, 0)
    for x in range(8):
      GPIO.output(self.PIN_DATA, (byte >> x) & 1)
      GPIO.output(self.PIN_CLOCK, 1)
      GPIO.output(self.PIN_CLOCK, 0)

  def latch(self):
    GPIO.output(self.PIN_LATCH, 1)

if __name__ == "__main__":
  sftr = shifter(16, 21, 20)
  for x in range(255):
    sftr.shiftout(x)
    time.sleep(1)
