# Commands

---

brightness [value] -

If value is specified, sets brightness to new value. Response contains value. value must be a number or the string 'auto'. Setting brightness to 'auto' enables auto-brightness using the light sensor. If value is a number, it is clamped to the range [0, 255]

---

initialize -

Initialize is an internal message used by the ClockControlThread to send intial configuration values to the ClockWorksThread which uses them to set up the BigDisplay

---

mode [ clock | timetemp | off ] - 

Set the display mode. 

* clock - show the time
* timetemp - alternate between time and temperature display
* off - no display

---

