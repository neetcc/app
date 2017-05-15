# -*- coding: utf-8 -*-

import sys

from ryu.cmd import manager


def main():
    sys.argv.append('oftroute.config')
    sys.argv.append('oftroute.flow')
    sys.argv.append('oftroute.trace')
    sys.argv.append('--enable-debugger')
    manager.main()


if __name__ == '__main__':
    main()
