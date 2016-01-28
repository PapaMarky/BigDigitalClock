#!/usr/bin/python
# Copyright 2016, Mark Dyer
import ClockControlThread
import ClockWorksThread

if __name__ == "__main__":
    threads = []
    # Start the threads
    clockworks_thread = ClockWorksThread.ClockWorksThread()
    threads.append(clockworks_thread)

    clockcontrol_thread = ClockControlThread.ClockControlThread()
    threads.append(clockcontrol_thread)

    for t in threads:
        t.join()

    print "Exiting"


