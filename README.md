# BigDigitalClock
Create a big 8 segment digital clock using LED strips for segments

## Shift Register Example
http://learn.pimoroni.com/tutorial/170pt-projects/the-shift-register-170pt

## Command Format ##

Q request

{'type': 'request', 'source':<handler thread>, 'msg': [...params...]}

{'type': 'response', 'source':<handler thread>, 'status': STATUS, 'detail': <None or "description">, 'msg': [...params...]}

{'type': 'notify', 'source': <None or handler thread>, 'msg': [...params...]}

STATUS: 'ok' | 'fail'

## Command Flow ##

ClockCLI
 |
 | client.send_message(msg)
\|/
ClockRequestHandler
 |
 | ClockServer.controller.handle(self, cur_thread, msg)
\|/
ClockControlThread
 |
 | self.display_q.put(request)
\|/
ClockWorksThread
 |
 | .run() -> .handle_job(job)
 |
 | self.control_q.put(results)
\|/
ClockControlThread.run()
 |
 | 