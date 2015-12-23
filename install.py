#!/usr/bin/python

import os, sys

euid = os.geteuid()
if euid != 0:
    print "Changing user to root..."
    args = ['sudo', sys.executable] + sys.argv + [os.environ]
    os.execlpe('sudo', *args)

print "****************************************"
print "*  Install Big Digital Clock"
print "****************************************"
print ""

print "Installing Application..."

print "Installing Service..."


