# Request Messages
Requests sent from client to server. 

## Mode Independent
Requests that will be handled independent of the current clock mode. Some requesests are mode dependant (see below) and only have effect when that mode is the current mode.

### Get / Set
`get` and `set` are used to get or set the value of various configuration parameters. The arguments specified below must be specified for `set` and will be returned in the response to `get`. The response to `set` will include the newly set values. Note that this may be different from the value requested.

**`brightness`** - 
set takes one argument which must be an integer or the string 'auto'. Integers are clamped to the range [0, 255].

**`brightness config`** `pwm_min` `pwm_max` `sensor_min` `sensor_max` -
Get or set the values used for mapping light sensor values to LED PWM (brightness) duty cycle.

**`mode`**  `clock` | `off` | `stopwatch` | `timer` -
Set the display mode.

**`clock show-seconds`** `True` | `False` -
In `clock` or `timetemp` determines whether seconds are displayed (HH:MM:SS) or not (HH:MM).

**`clock zero-pad-hour`** `True` | `False` -
In clock mode, if `True`, hours less than 10 are padded with zero. (ex. "01:35:00"). If `False`, hours less than 10 are padded with a space. (ex. " 1:35:00")

**`clock show-temp`** `True` | `False` -
In clock mode, Show the current temperature alternating with 

## Clock Mode
## Stopwatch Mode
**`start`** - Start counting elapsed time

**`stop`** - Stop counting elapsed time. returns current elapsed time.

**`clear`** - Reset elapsed time to zero. No return value.

**`lap`** - Continue counting elapsed time. Returns current elapsed time.

## Timer Mode
**`duration`** `seconds` - time to countdown from

**`start`** - Start (or resume) counting down

**`pause`** - Pause countdown

**`cancel`**

# Notification Messages
Messages sent from the Server to the clients.

# Internal Messages
Messages sent between threads in the server.

**`initialize`** - 
Initialize is an internal message used by the ClockControlThread to send intial configuration values to the ClockWorksThread which uses them to set up the BigDisplay

