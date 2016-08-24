#!/usr/bin/env python
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import sys
sys.path.append('/home/pi/BigDigitalClock/src')
import ClockClient
import json

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None
clk_server_state = 'UNSET'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    print "START background_thread"
    while True:
        line = client.check_for_message()

        if line is not None and line != '':
            print "LINE: {}".format(line)
            #msg = json.loads(line)
            #m = msg['msg']
            #value = msg['value']
            #print "MSG: {}".format(str(msg))
            count += 1
            socketio.emit('initialize', {'data': line, 'count': count}, namespace='/test')
        else:
            socketio.sleep(0.1)
            
        # socketio.sleep(10)
        # count += 1
        # socketio.emit('my response',
        #               {'data': 'Server generated event', 'count': count},
        #               namespace='/test')

@app.route('/')
def index():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    state = 'NONE'
    if client.is_connected():
        state = 'CONNECTED'
    else:
        state = 'NOT CONNECTED'

    return render_template('index.html', async_mode=socketio.async_mode, clk_server_state=state)

@socketio.on('get config', namespace='/test')
def get_config():
    session['receive_count'] = session.get('receive_count', 0) + 1
    if client.is_connected():
        status, msg = client.handle_request('get config')
        if not status:
            emit('config', msg)
        else:
            emit('config', msg)

@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})

@socketio.on('brightness', namespace='/test')
def brightness_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    
    b = 'set brightness '
    if message['data']['auto_brightness']:
        b = b + 'auto'
    else:
        b = b + str(message['data']['brightness'])
    client.handle_request(b)

    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(rooms()),
          'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('my ping', namespace='/test')
def ping_pong():
    emit('my pong')


@socketio.on('connect', namespace='/test')
def test_connect():
    config = None
    data = {'data': 'Connected', 'count': 0}
    if client.is_connected():
        status, msg = client.handle_request('get all')
        data['status'] = status
    emit('my response', data)


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    id = 'ClockWebAppClient'
    client = ClockClient.ClockClient(id)
    socketio.run(app, debug=True, host='0.0.0.0')
