import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
PIN_DATA  = 16
PIN_LATCH = 21
PIN_CLOCK = 20
GPIO.setup(PIN_DATA,  GPIO.OUT)
GPIO.setup(PIN_LATCH, GPIO.OUT)
GPIO.setup(PIN_CLOCK, GPIO.OUT)

def shiftout(byte):
  GPIO.output(PIN_LATCH, 0)
  for x in range(8):
    GPIO.output(PIN_DATA, (byte >> x) & 1)
    GPIO.output(PIN_CLOCK, 1)
    GPIO.output(PIN_CLOCK, 0)
  GPIO.output(PIN_LATCH, 1)

for x in range(255):
  shiftout(x)
  time.sleep(1)
