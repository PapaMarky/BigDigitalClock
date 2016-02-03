# Copyright 2016, Mark Dyer
import sys
import socket
import errno
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

    def __init__(self, socket):
        ConnectionThread.THREAD_COUNT = ConnectionThread.THREAD_COUNT + 1
        thread_name = 'ConnectionThread-{}'.format(ConnectionThread.THREAD_COUNT)
        super(ConnectionThread, self).__init__(name=thread_name)
        self.socket = socket
        self.socket.setblocking(False)

        self.logger = logging.getLogger('BigClock.' + thread_name)
        if ConnectionThread.connections is not None:
            ConnectionThread.connections.append(self)
        self.task_q = Queue.Queue()

    def finish(self):
        if ConnectionThread.connections is not None:
            ConnectionThread.connections.remove(self)

    def shutdown(self):
        self.logger.info('shutdown')
        self.send_message('shutdown')
        self.running = False

    def send_message(self, message):
        self.logger.debug("send_message: '%s'", message)
        self.socket.sendall(message)

    def handle_task(self, task):
        if task.has_key('type') and task['type'] == 'response':
            task.pop('type', None)
            task.pop('connection', None)
            self.logger.info("Handling response: %s", str(task))
            response = json.dumps(task)
            self.logger.info("Handling response: %s", response)
            self.send_message(response)

    def queue_task(self, task):
        self.task_q.put(task)

    def check_for_request(self):
        try:
            request = self.socket.recv(1024)
        except socket.error, e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
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
                    request = json.loads(request)
                    request['connection'] = self
                    if ClockServer.controller is not None:
                        ClockServer.controller.queue_task(request)
            except:
                self.logger.error("Exception on %s, %s: '%s'",
                             threading.current_thread().name,
                             sys.exc_info()[0],
                             sys.exc_info()[1])
                return

            while not self.task_q.empty():
                task = self.task_q.get()
                self.handle_task(task)

            if request == 'shutdown':
                self.shutdown_all()
                self.running = False
                return
            if request == 'done':
                return

class ClockServer(threading.Thread):

    controller = None

    def __init__(self, controller, host, port):
        ClockServer.controller = controller
        super(ClockServer, self).__init__(name='ServerThread')
        self.logger = logging.getLogger('BigClock.ServerThread')
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.daemon = True

    def shutdown(self):
        if self.socket is not None:
            self.socket.shutdown()
            self.socket.close()
        self.running = False

    def run(self):
        self.logger.info("Running Server Thread")
        self.running = True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger.info("Created Server: %s : %s", self.host, self.port)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

        while self.running:
            (clientsocket, address) = self.socket.accept()
            self.logger.info("Connection from %s", address)
            ct = ConnectionThread(clientsocket)
            ct.start()
            
    def notify_all(self, sender, msg):
        for handler in ConnectionThread.connections:
            handler.request.sendall(msg)
