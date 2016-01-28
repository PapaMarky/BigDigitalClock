#!/usr/bin/python
# Copyright 2016, Mark Dyer

from threading import Thread

class ClockControlThread(Thread):
    def __init__(self):
        super(ClockControlThread, self).__init__()

    def run(self):
        print "ClockControlThread Starting"

