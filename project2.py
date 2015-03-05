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
parser.add_option("-b", "--be-host", dest="host", action="store_true")
parser.add_option("-d", "--destination", dest="destination")
parser.add_option("-p", "--port", type="int", dest="port")
parser.add_option("-r", "--protocol", dest="protocol")
parser.add_option("-s", "--sample-latency", type="int", dest="sample_latency")
options = parser.parse_args()[0]

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
            try:
                sock.send(data)
            except:
                break

    sock.close()


def receive_thread(host, port):
    receive_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    receive_socket.bind((host, port))
    receive_socket.listen(1)
    connection, address = receive_socket.accept()
    print "%s connected on port %d." % address
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
    return send_thread

try:
    if options.host:
        receive_thread('', options.port)
        sleep(1)
        t = send_thread(options.destination, options.port + 1)

    else:
        t =send_thread(options.destination, options.port)
        receive_thread('', options.port + 1)

    t.join()

except:
    print "Exiting."
