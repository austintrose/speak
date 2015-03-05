from socket import *
import random
import alsaaudio
from optparse import OptionParser
from threading import Thread
from time import sleep


def parse_parameters():
    """
    :return: A dictionary of the parameters specified at the command line.

    """

    parser = OptionParser()

    # Exactly one of the two people connecting must include this flag, and that person must run program before their partner does.
    parser.add_option("-b", "--be-host", dest="host", action="store_true")

    # IPv4 address to connect to.
    parser.add_option("-d", "--destination", dest="destination")

    # Port to connect with. This port AND THE ONE IMMEDIATELY AFTER IT will be used.
    parser.add_option("-p", "--port", type="int", dest="port")

    # Protocols either TCP or UDP
    parser.add_option("-r", "--protocol", dest="protocol")

    # Millisecond latency in sampling the audio device.
    parser.add_option("-s", "--sample-latency", type="int", dest="sample_latency")

    # Millisecond latency in sampling the audio device.
    parser.add_option("-l", "--loss", type="int", dest="loss")

    options = parser.parse_args()[0]
    options.sample_latency = options.sample_latency / 1000.0

    return options

options = parse_parameters()

def configure_device(d):
    d.setchannels(1)
    d.setrate(8000)
    d.setformat(alsaaudio.PCM_FORMAT_U8)
    d.setperiodsize(160)

def receive_and_play(read_function):
    device = alsaaudio.PCM(type=alsaaudio.PCM_PLAYBACK,
                           mode=alsaaudio.PCM_NONBLOCK,
                           card="default")

    configure_device(device)

    while True:
        sleep(options.sample_latency)
        data = read_function()

        # Percent chance to artificially "lose" the packet.
        if options.loss > 0:
            if random.random() * 100 < options.loss:
                continue

        if data:
            device.write(data)

def record_and_send(write_function):
    device = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE,
                           mode=alsaaudio.PCM_NONBLOCK,
                           card='default')

    configure_device(device)

    while True:
        l, data = device.read()

        try:
            if l:
                write_function(data)
        except:
            break

def receive_thread(host, port):
    if options.protocol == "TCP":
        receive_socket = socket(AF_INET,SOCK_STREAM)
        receive_socket.bind((host, port))
        receive_socket.listen(1)
        connection, address = receive_socket.accept()
        print "%s connected on port %d." % address
        receive_socket.setblocking(0)
        read_function = lambda: connection.recv(1024)

    elif options.protocol == "UDP":
        receive_socket = socket(AF_INET, SOCK_DGRAM)
        receive_socket.bind((host, port))
        receive_socket.setblocking(0)
        read_function = lambda: receive_socket.recvfrom(1024)

    receive_thread = Thread(target=receive_and_play, args=(read_function,))
    receive_thread.setDaemon(True)
    receive_thread.start()

def send_thread(host, port):
    if options.protocol == "TCP":
        send_socket = socket(AF_INET, SOCK_STREAM)
        send_socket.connect((host, port))
        send_socket.setblocking(0)
        write_function = send_socket.send
        
    elif options.protocol == "UDP":
        send_socket = socket(AF_INET, SOCK_DGRAM)
        write_function = lambda x: send_socket.sendto(x, (host, port))

    send_thread = Thread(target=record_and_send, args=(write_function,))
    send_thread.setDaemon(True)
    send_thread.start()

try:
    if options.host:
        receive_thread('', options.port)
        sleep(1)
        send_thread(options.destination, options.port + 1)

    else:
        send_thread(options.destination, options.port)
        receive_thread('', options.port + 1)

    while True:
        pass

except:

    print "Exiting."
