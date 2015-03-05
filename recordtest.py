#!/usr/bin/env python

## python recordtest.py out.raw # talk to the microphone
## aplay -r 8000 -f U8 -c 1 out.raw

import sys
import time
import getopt
import alsaaudio

if __name__ == '__main__':

    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, 'default')

    inp.setchannels(1)
    inp.setrate(8100)
    inp.setformat(alsaaudio.PCM_FORMAT_U8)
    inp.setperiodsize(160)

    while True:
        l, data = inp.read()
        if l:
            sys.stdout.write(data)
            time.sleep(.001)
