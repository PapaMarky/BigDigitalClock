# copyright 2016, Mark Dyer

VALID_COMMANDS = ['get', 'set', 'shutdown']
VALID_CONFIGS = ['brightness', 'mode', 'clock']
VALID_CLOCK_CONFIGS = ['show-seconds', 'zero-pad-hour', 'show-temp']

VALID_MODES = ['off', 'clock', 'timetemp']

def create_request(source, msg):
    return {'type': 'request',
            'source': source,
            'msg': msg}
