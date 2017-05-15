# -*- coding: utf-8 -*-

import sys

from ryu.cmd import manager


def main():
    sys.argv.append('config')
    sys.argv.append('flow')
    sys.argv.append('trace')
    manager.main()


if __name__ == '__main__':
    main()
