#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from ryu.cmd import manager


def main():
    sys.argv.append('--ofp-tcp-listen-port')
    sys.argv.append('6653')
    #sys.argv.append('shortest_forwarding')
    #sys.argv.append('network_awareness')
    #sys.argv.append('--verbose')
    #sys.argv.append('ofctl_rest.py')
    #sys.argv.append('rest_topology')
    sys.argv.append('shortestpath.py')
    #sys.argv.append('trace.py')
    sys.argv.append('--observe-links')
    #sys.argv.append('ryu.topology.dumper')
    #sys.argv.append('--k-paths=2')
    #sys.argv.append('--weight=bw')
    sys.argv.append('--enable-debugger')
    manager.main()

if __name__ == '__main__':
    main()