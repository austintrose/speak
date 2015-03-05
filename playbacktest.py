#!/usr/bin/env python

import sys
import alsaaudio

if __name__ == '__main__':
    out = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                        mode=alsaaudio.PCM_NONBLOCK,
                        card="default")

    out.setchannels(1)
    out.setrate(8000)
    out.setformat(alsaaudio.PCM_FORMAT_U8)
    out.setperiodsize(160)

    # Read data from stdin
    data = sys.stdin.read(320)
    while data:
        out.write(data)
        data = sys.stdin.read(320)


