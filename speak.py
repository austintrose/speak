import alsaaudio
import os
import threading
import sys
from optparse import OptionParser
from math import sqrt
import struct

CHUNK_MS = 20 # 20ms chunks sent at a time
BYTES_PER_MS = 8 # 8 bytes per millisecond
BYTES_PER_CHUNK = CHUNK_MS * BYTES_PER_MS
SILENCE_BYTES = 100 * BYTES_PER_MS
PING = "SPEAK\n"

def parse_args():

    defaults = {
        "host": None,
        "port": 9999,
        "protocol": "TCP",
        "sample_interval": 20
    }

    parser = OptionParser()

    parser.add_option("-t", "--host", dest="host", metavar="HOST",
                      default=None,
                      help="IPV4 address or hostname to connect to.")

    parser.add_option("-p", "--port", dest="port", metavar="PORT",
                      default=defaults["port"],
                      help="Port to connect to. Default: %d." % defaults["port"])

    parser.add_option("-r", "--protocol", dest="protocol", metavar="PROTOCOL",
                      default=defaults["protocol"],
                      help="Protcol to communicate with. TCP or UDP. Default: %s."
                           % defaults["protocol"])

    parser.add_option("-s", "--sample-interval", dest="sample_interval",
                      metavar="SAMPLE_INTERVAL",
                      default=defaults["sample_interval"],
                      help="Audio sampling interval in milliseconds. Default: %d."
                           % defaults["sample_interval"])

    (options, args) = parser.parse_args()

    options.port = int(options.port)
    options.sample_interval = int(options.port)

    return options

def mean(x):
    "https://www.physics.rutgers.edu/~masud/computing/WPark_recipes_in_python.html"
    n, mean, = len(x), 0
    for a in x:
        mean = mean + a
        mean = mean / float(n)
    return mean

class Recorder(object):

    upper_threshold = None

    def __init__(self):
        device = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK, 'default')
        device.setchannels(1)
        device.setrate(8000)
        device.setformat(alsaaudio.PCM_FORMAT_U8)
        device.setperiodsize(160)
        r, w = os.pipe()

        self.device = device
        self.pipe_in = os.fdopen(w, 'w')
        self.pipe_out = os.fdopen(r)

    def computer_upper_threshold(self, silence):
        unsigned_values = [struct.unpack('B', s)[0] for s in silence]
        magnitudes = [abs(128 - v) for v in unsigned_values]

        energies = []
        for i in xrange(len(magnitudes) - 10 * BYTES_PER_MS):
            l = magnitudes[i:i+10*BYTES_PER_MS]
            energies.append(sum(l))

        imx = max(energies)
        imn = mean(energies)
        i1 = 0.03 * (imx - imn) + imn
        i2 = 4 * imn
        itl = min(i1, i2)
        return 5 * itl

    def record_loop(self):

        buffer = b""
        while True:
            l, data = self.device.read()

            if l:
                buffer += data

                if self.upper_threshold is None:
                    if len(buffer) >= SILENCE_BYTES:
                        self.upper_threshold = self.computer_upper_threshold(buffer[:SILENCE_BYTES])
                        buffer = buffer[SILENCE_BYTES:]

                else:
                    if len(buffer) >= BYTES_PER_CHUNK:
                        chunk, buffer = buffer[:BYTES_PER_CHUNK], buffer[BYTES_PER_CHUNK:]

                        for c in chunk:
                            magnitude = abs(128 - struct.unpack('B', c)[0])
                            if magnitude > self.upper_threshold:
                                self.pipe_in.write(chunk)
                                self.pipe_in.flush()
                            break

class Player(object):

    def __init__(self):
        device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                               mode=alsaaudio.PCM_NONBLOCK,
                               card="default")
        device.setrate(8000)
        device.setformat(alsaaudio.PCM_FORMAT_U8)
        device.setperiodsize(160)

        self.device = device

        r, w = os.pipe()
        self.pipe_in = os.fdopen(w, 'w')
        self.pipe_out = os.fdopen(r)

    def play_loop(self):
        buffer = b""

        while True:
            check = self.pipe_out.read(BYTES_PER_CHUNK)
            if check is not None:
                buffer += check

            if len(buffer) >= BYTES_PER_CHUNK:
                chunk, buffer = buffer[:BYTES_PER_CHUNK], buffer[BYTES_PER_CHUNK:]
                self.device.write(chunk)

options = parse_args()
recorder = Recorder()
player = Player()

record_thread = threading.Thread(target=Recorder.record_loop, args=(recorder,))
record_thread.setDaemon(True)
record_thread.start()

# play_thread = threading.Thread(target=Player.play_loop, args=(player,))
# play_thread.setDaemon(True)
# play_thread.start()

while True:
    data = recorder.pipe_out.read(BYTES_PER_CHUNK)
    if data is not None:
        sys.stdout.write(data)

def record
