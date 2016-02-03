# copyright 2016, Mark Dyer

def create_request(source, msg):
    return {'type': 'request',
            'source': source,
            'msg': msg}
