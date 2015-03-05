import socket
import sys
import alsaaudio
import subprocess
from optparse import OptionParser
from threading import Thread
from time import sleep

defaults = {
    "host": None,
    "port": 9999,
    "protocol": "TCP",
    "sample_latency": 20
}

parser = OptionParser()

parser.add_option("-t", "--host", dest="host", metavar="HOST",
                  default=defaults['host'],
                  help="IPV4 address or hostname to connect to.")

parser.add_option("-p", "--port", dest="port", metavar="PORT",
                  default=defaults["port"],
                  help="Port to connect to. Default: %d." % defaults["port"])

parser.add_option("-r", "--protocol", dest="protocol", metavar="PROTOCOL",
                  default=defaults["protocol"],
                  help="Protcol to communicate with. TCP or UDP. Default: %s."
                       % defaults["protocol"])

parser.add_option("-s", "--sample-latency", dest="sample_latency",
                  metavar="SAMPLE_LATENCY",
                  default=defaults["sample_latency"],
                  help="Audio sampling latency in milliseconds. Default: %d."
                       % defaults["sample_latency"])

options, _ = parser.parse_args()
options.port = int(options.port)
options.sample_interval = int(options.port)

def receive_and_play(host, port):
    receive_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    receive_socket.bind((host, port))
    receive_socket.listen(1)
    connection, address = receive_socket.accept()

    send_thread(address)

    device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                           mode=alsaaudio.PCM_NONBLOCK,
                           card="default")

    device.setchannels(1)
    device.setrate(8000)
    device.setformat(alsaaudio.PCM_FORMAT_U8)
    device.setperiodsize(160)

    while True:
        data = connection.recv(1024)
        if data:
            device.write(data)

    connection.close()


def record_and_send(host, port):
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_socket.connect((host, port))

    receive_thread('', port)

    device = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE,
                           mode=alsaaudio.PCM_NONBLOCK,
                           card='default')

    device.setchannels(1)
    device.setrate(8000)
    device.setformat(alsaaudio.PCM_FORMAT_U8)
    device.setperiodsize(160)

    while True:
        l, data = device.read()
        if l:
            send_socket.send(data)

    send_socket.close()


def receive_thread(host, port):
    receive_thread = Thread(target=receive_and_play, args=('', options.port))
    receive_thread.setDaemon(True)
    receive_thread.start()

def send_thread(host, port):
    send_thread = Thread(target=record_and_send, args=(host, port))
    send_thread.setDaemon(True)
    send_thread.start()

if options.host is None:
    receive_thread('', options.port)
else:
    send_thread(options.host, options.port)

while True:
    pass
