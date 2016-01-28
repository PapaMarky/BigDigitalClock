#!/usr/bin/python
# Copyright 2016, Mark Dyer

from threading import Thread

class ClockWorksThread(Thread):
    def __init__(self):
        super(ClockWorksThread, self).__init__()

    def run(self):
        print "ClockWorksThread Starting"
