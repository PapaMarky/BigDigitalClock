# copyright 2016, Mark Dyer

VALID_MODES = ['off', 'clock', 'timetemp']

def create_request(source, msg):
    return {'type': 'request',
            'source': source,
            'msg': msg}
