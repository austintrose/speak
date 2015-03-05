import socket
import sys
import alsaaudio
import subprocess
from optparse import OptionParser
from threading import Thread
from time import sleep

defaults = {
    "host": None,
    "job": "host",
    "port": 9999,
    "protocol": "TCP",
    "sample_latency": 20
}

parser = OptionParser()

parser.add_option("-j", "--job", dest="job", metavar="JOB",
                  default=defaults['job'],
                  help="host or client.")

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

def receive_and_play(connection):
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


def record_and_send(sock):
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
            sock.send(data)

    sock.close()


def receive_thread(host, port):
    receive_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    receive_socket.bind((host, port))
    receive_socket.listen(1)
    connection, address = receive_socket.accept()
    receive_socket.setblocking(0)

    receive_thread = Thread(target=receive_and_play, args=(connection,))
    receive_thread.setDaemon(True)
    receive_thread.start()

def send_thread(host, port):
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    send_socket.connect((host, port))
    send_socket.setblocking(0)

    send_thread = Thread(target=record_and_send, args=(send_socket,))
    send_thread.setDaemon(True)
    send_thread.start()

if options.job is "host":
    receive_thread('', options.port)
    send_thread(options.host, options.port + 1)

else:
    send_thread(options.host, options.port)
    receive_thread('', options.port + 1)

while True:
    pass
