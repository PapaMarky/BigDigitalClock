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

class ConnectionThread(threading.Thread):
    THREAD_COUNT = 0
        
    def __init__(self, socket, server):
        ConnectionThread.THREAD_COUNT = ConnectionThread.THREAD_COUNT + 1
        thread_name = 'ConnectionThread-{}'.format(ConnectionThread.THREAD_COUNT)
        super(ConnectionThread, self).__init__(name=thread_name)
        self.socket = socket
        self.socket.setblocking(False)
        self.server = server

        self.logger = logging.getLogger('BigClock.' + thread_name)
        self.task_q = Queue.Queue()

        self.shuttingdown = False

    # call shutdown() when the server is being shutdown,
    # otherwise call stop()
    def shutdown(self):
        self.logger.info('*** SHUTDOWN ***')
        self.shuttingdown = True

    # call stop() when ending this connection
    def stop(self):
        self.logger.info('stop() called')
        self.running = False
        
    def send_message(self, message):
        self.logger.debug("send_message: '%s'", message)
        self.socket.sendall(message)

    # handle a task - tasks come via the task_q
    def handle_task(self, task):
        if 'type' in task and task['type'] in ['response', 'notify']:
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
                return None
            else:
                self.logger.error("check_for_request Exception: %s", e)
                self.stop()
                return None
        self.logger.debug("Got Request: %s", request)
        if request == '':
            # empty request means the connection went away
            self.stop()
            return None
        return request

    def run(self):
        self.running = True

        self.thread = threading.current_thread()
        while self.running:
            request = None
            try:
                request = self.check_for_request()
                if request is not None:
                    self.logger.debug("%s Got '%s'", self.thread.name, str(request))
                    if request != '':
                        request = json.loads(request)
                        request['connection'] = self
                        if ClockServer.controller is not None:
                            ClockServer.controller.queue_task(request)
                    else:
                        self.logger.info('Got empty request')
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

        self.logger.info('%s: connection closed. server shutdown: %s', self.thread.name, str(self.shuttingdown))
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

    def shutdown(self):
        self.logger.info('shutdown')
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                self.socket = None
            except:
                pass # we're shutting down. Ignore exceptions
        self.logger.info('stopping for shutdown')
        self.running = False

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
            self.shutdown()
            return

        read_list = [self.socket]

        while self.running:
            try:
                readable, writeable, errored = select.select(read_list, [], [], 0)
            except Exception, e:
                self.logger.error("Select Exception: %s", e)
                self.shutdown()
                continue

            for s in readable:
                try:
                    self.logger.info('Socket is readable')
                    (clientsocket, address) = self.socket.accept()
                    self.logger.info("Connection from %s", address)
                    ct = ConnectionThread(clientsocket, self)
                    ct.start()
                except Exception, e:
                    self.logger.error("Accept Exception: %s", e)
                    self.shutdown()

        self.logger.info('no longer running')
