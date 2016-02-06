# Copyright 2016, Mark Dyer
import sys
import socket
import errno
import select
import ClockClient
import logging
import threading
import json
import Queue

#logger = logging.getLogger('BigClock.Server')

class ConnectionThread(threading.Thread):
    connections = []
    THREAD_COUNT = 0
        
    def shutdown_all(self):
        self.logger.info("shutdown_all")
        for h in ConnectionThread.connections:
            h.shutdown()

    def __init__(self, socket, server):
        ConnectionThread.THREAD_COUNT = ConnectionThread.THREAD_COUNT + 1
        thread_name = 'ConnectionThread-{}'.format(ConnectionThread.THREAD_COUNT)
        super(ConnectionThread, self).__init__(name=thread_name)
        self.socket = socket
        self.socket.setblocking(False)
        self.server = server

        self.logger = logging.getLogger('BigClock.' + thread_name)
        if ConnectionThread.connections is not None:
            ConnectionThread.connections.append(self)
        self.task_q = Queue.Queue()

        self.shuttingdown = False

    def finish(self):
        if ConnectionThread.connections is not None:
            ConnectionThread.connections.remove(self)

    def shutdown(self):
        self.logger.info('*** SHUTDOWN ***')
        self.running = False
        self.shuttingdown = True

    def send_message(self, message):
        self.logger.debug("send_message: '%s'", message)
        self.socket.sendall(message)

    def handle_task(self, task):
        if task.has_key('type') and (task['type'] == 'response' or task['type'] == 'notify'):
            task.pop('connection', None)
            cmd = task['msg'][0]

            self.logger.info("Handling response: %s", str(task))
            response = json.dumps(task)
            self.send_message(response)

            if cmd == 'shutdown':
                self.shutdown()

    def queue_task(self, task):
        self.task_q.put(task)

    def check_for_request(self):
        try:
            request = self.socket.recv(1024)
        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                # self.logger.debug('Socket would block')
                return None
            elif err == 57:
                self.logger.error('Socket is no longer connected')
                self.running = False
                return None
            else:
                self.logger.error("check_for_request Exception: %s", e)
                return None
        self.logger.debug("Got Request: %s", request)
        return request

    def run(self):
        self.running = True

        self.thread = threading.current_thread()
        while self.running:
            request = None
            try:
                request = self.check_for_request()
                if request is not None:
                    self.logger.debug("Got '%s'", str(request))
                    self.logger.debug("cur_thread '%s'", self.thread)
                    if request != '':
                        request = json.loads(request)
                        request['connection'] = self
                        if ClockServer.controller is not None:
                            ClockServer.controller.queue_task(request)
                    else:
                        self.stop()
            except:
                name = 'NO THREAD'
                if threading:
                    name = threading.cur_thread()
                    self.logger.error("Exception on %s, %s: '%s'",
                                      name,
                                      sys.exc_info()[0],
                                      sys.exc_info()[1])
                else:
                    self.logger.error("Exception")
                return

            while not self.task_q.empty():
                task = self.task_q.get()
                self.handle_task(task)

        self.logger.info('connection closed. server shutdown: %s', str(self.shuttingdown))
        if self.shuttingdown:
            self.server.shutdown()

class ClockServer(threading.Thread):

    controller = None

    def __init__(self, controller, host, port):
        ClockServer.controller = controller
        super(ClockServer, self).__init__(name='ServerThread')
        self.logger = logging.getLogger('BigClock.ServerThread')
        self.host = host
        self.port = port
        self.socket = None
        self.running = True
        #self.daemon = True

    def stop(self):
        self.logger.info('stop() called')
        self.running = False

    def shutdown(self):
        self.logger.info('shutdown')
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                self.socket = None
            except:
                pass # we're shutting down. Ignore exceptions
        self.stop()

    def run(self):
        self.logger.info("Running Server Thread")
        self.running = True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.logger.info("Created Server: %s : %s", self.host, self.port)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
        except Exception, e:
            self.logger.error("socket exception: %s", e)
            self.stop()
            return

        read_list = [self.socket]

        while self.running:
            readable, writeable, errored = select.select(read_list, [], [])

            for s in readable:
                (clientsocket, address) = self.socket.accept()
                self.logger.info("Connection from %s", address)
                ct = ConnectionThread(clientsocket, self)
                ct.start()

        self.logger.info('no longer running')
            
    def notify_all(self, sender, msg):
        for handler in ConnectionThread.connections:
            handler.request.sendall(msg)

