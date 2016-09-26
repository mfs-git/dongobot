# -*- coding: utf-8 -*-

import logging
import DongobotServer
import sys

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    token = sys.argv[1]
    server = DongobotServer.DongobotServer(token)
    server.run()

if __name__ == "__main__":
    main()
