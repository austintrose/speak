Austin Rose
CS529 Project 2

This project is entirely done in Python, and I ran it using Python 2.7.6 on Ubuntu 14.04 64-bit.

Before the project could run, the Ubuntu installation needed a few additional things:
    TODO

In order to chat, two users A and B should something similar to the following:

    User A (at 10.0.0.15):
    $ python speak.py --be-host --destination 10.0.0.16 --port 9999 --protocol TCP --sample-latency 10 --loss 0

    User B (at 10.0.0.16):
    $ python speak.py --destination 10.0.0.15 --port 9999 --protocol --sample-latency 20 --loss 0

The following constraints apply:
    - Exactly one of the two users should use the "--be-host" flag, and that user should run their client first.
    - The "--destination" flags must have each-others IPv4 address to connect to.
    - The port specified will be used, IN ADDITION TO THE FOLLOWING PORT. So in the above example, ports 9999 and 10000 must both be open for use.
    - The "--protocol" flag can take either TCP or UDP.
    - The "--sample-latency" flag is measured in milliseconds.
    - The "--loss" flag must give an integer percentage 0 to 100.