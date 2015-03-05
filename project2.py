from socket import *
import random
from optparse import OptionParser
from threading import Thread
from time import sleep
from struct import unpack

from alsaaudio import *


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
    d.setformat(PCM_FORMAT_U8)
    d.setperiodsize(160)


def receive_and_play(read_function):
    """
    Open up the audio device for playback, and supply input by looping over the given function.

    """

    device = PCM(type=PCM_PLAYBACK, mode=PCM_NONBLOCK, card="default")
    configure_device(device)

    while True:

        sleep(options.sample_latency)

        try:
            data = read_function()
        except:
            continue

        # Percent chance to artificially "lose" the packet.
        if options.loss > 0:
            if random.random() * 100 < options.loss:
                continue

        if data:
            device.write(data)


def record_and_send(write_function):
    """
    Open up the audio device for playback, and call the given function with each chunk sampled.

    """

    device = PCM(type=PCM_CAPTURE, mode=PCM_NONBLOCK, card='default')
    configure_device(device)

    upper_threshold = None
    silence_buffer = ""

    while True:
        success, data = device.read()

        try:
            if not success:
                continue

            if upper_threshold is None:
                silence_buffer += data

                if len(silence_buffer) >= 800:
                    upper_threshold = get_upper_threshold(silence_buffer[:800])

            else:
                write_function(data)

        except:
            break


def mean(x):
    n, mean, = len(x), 0
    for a in x:
        mean = mean + a
        mean = mean / float(n)
    return mean


def get_upper_threshold(silence_data):
    magnitudes = [abs(128-unpack('B', s)[0]) for s in silence_data]

    energies = []
    for i in xrange(len(magnitudes) - 80):
        l = magnitudes[i:i+80]
        energies.append(sum(l))

    imx = max(energies)
    imn = mean(energies)
    i1 = 0.03 * (imx - imn) + imn
    i2 = 4 * imn
    itl = min(i1, i2)
    itu = 5 * itl
    print "lower", itl, "upper", itu
    return itu

def create_receiving_thread(host, port):
    """
    Spawn a thread which will listen for a voice stream at the given address and forward whatever is received for playback on the audio device.

    """

    if options.protocol == "TCP":
        receive_socket = socket(AF_INET,SOCK_STREAM)
        receive_socket.bind((host, port))
        receive_socket.listen(1)

        connection, address = receive_socket.accept()
        read_function = lambda: connection.recv(1024)

    elif options.protocol == "UDP":
        receive_socket = socket(AF_INET, SOCK_DGRAM)
        receive_socket.bind((host, port))

        read_function = lambda: receive_socket.recvfrom(1024)[0]

    receive_socket.setblocking(0)

    receive_thread = Thread(target=receive_and_play, args=(read_function,))
    receive_thread.setDaemon(True)
    receive_thread.start()


def create_sending_thread(host, port):
    """
    Spawn a thread which will record from the audio device and send samples to the given address.

    """

    if options.protocol == "TCP":
        send_socket = socket(AF_INET, SOCK_STREAM)
        send_socket.connect((host, port))

        write_function = send_socket.send

    elif options.protocol == "UDP":
        send_socket = socket(AF_INET, SOCK_DGRAM)

        write_function = lambda x: send_socket.sendto(x, (host, port))

    send_socket.setblocking(0)

    send_thread = Thread(target=record_and_send, args=(write_function,))
    send_thread.setDaemon(True)
    send_thread.start()


try:
    if options.host:

        # Receive partners connection.
        create_receiving_thread('', options.port)

        # Wait a second for partner to start listening for their receiving connection.
        sleep(1)

        # Start sending to partner.
        create_sending_thread(options.destination, options.port + 1)

    else:
        # Start sending to partner.
        create_sending_thread(options.destination, options.port)

        # Listen for connection from partner.
        create_receiving_thread('', options.port + 1)

    # Idle because the main thread is now done, but must stick around for Ctrl-C power.
    while True:
        pass

except:
    print "\nExiting."
