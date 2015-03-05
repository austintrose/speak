Austin Rose
CS529 Project 2

This project is entirely done in Python, and I ran it using Python 2.7.6 on Ubuntu 14.04 64-bit.

Before the project could run, the Ubuntu installation needed a few additional things:
    $ sudo apt-get install python-dev
    $ sudo pip install pyalsaaudio

In order to chat, two users A and B should something similar to the following:

    User A (at 10.0.0.15):
    $ python speak.py --be-host --destination 10.0.0.16 --port 9999 --protocol TCP --sample-latency 10 --loss 0

    User B (at 10.0.0.16):
    $ python speak.py --destination 10.0.0.15 --port 9999 --protocol TCP --sample-latency 20 --loss 0 --filter-silence

The following constraints apply:

    - Exactly one of the two users should use the "--be-host" flag, and that user should run their client first.

    - The "--destination" flags must have each-others IPv4 address to connect to.

    - The port specified will be used, IN ADDITION TO THE FOLLOWING PORT. So in the above example, ports 9999 and 10000
      must both be open for use.

    - The "--protocol" flag can take either TCP or UDP, but each person must use the same.

    - The "--sample-latency" flag is measured in milliseconds.

    - The "--loss" flag must give an integer percentage 0 to 100.

    - The "--filter-silence" flag is the ONLY optional parameter. If it is provided, the upper energy threshold from
      the previous assignment's algorithm is used to detect voice chunks to transmit.


Each flag can be abbreviated:
    -b : --be-host
    -d : --destination
    -p : --port
    -r : --protocol
    -s : --sample-latency
    -l : --loss
    -f : --filter-silence

Following are some other valid examples of startup conditions:

    User A (at 10.0.0.15):
    $ python speak.py --be-host --destination 10.0.0.16 --port 9999 --protocol UDP --sample-latency 0 --loss 10
    User B (at 10.0.0.16):
    $ python speak.py --destination 10.0.0.15 --port 9999 --protocol UDP --sample-latency 0 --loss 10

    User A (at 10.0.0.15):
    $ python speak.py -b -d 10.0.0.16 -p 9999 -r TCP -s 10 -l 10 -f
    User B (at 10.0.0.16):
    $ python speak.py -d 10.0.0.15 -p 9999 -r TCP -s 10 -l 5 -f
