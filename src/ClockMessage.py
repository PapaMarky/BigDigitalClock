# copyright 2016, Mark Dyer

VALID_COMMANDS = ['get', 'set', 'shutdown']
VALID_CONFIGS = ['brightness', 'mode', 'clock', 'temp']
VALID_GET_CONFIGS = ['all']
VALID_CLOCK_CONFIGS = ['show_seconds', 'zero_pad_hour', 'show_temp']
VALID_TEMP_CONFIGS = ['scale']

VALID_MODES = ['off', 'clock']

def str_to_bool(s):
    if isinstance(s, int):
        return bool(s)
    if s.lower() in ('1', 't', 'true'):
        return True
    elif s.lower() in ('0', 'f', 'false'):
        return False
    return None

def create_request(source, msg):
    return {'type': 'request',
            'source': source,
            'msg': msg}
