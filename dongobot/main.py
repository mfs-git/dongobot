# -*- coding: utf-8 -*-

import DongobotServer
import logging.handlers
import logging
import sys


logger = logging.root
logger.setLevel(logging.DEBUG)


# ch = logging.StreamHandler(stream=sys.stderr)
# ch.setLevel(logging.DEBUG)

sysloghandler = logging.handlers.SysLogHandler(address='/dev/log')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
syslogformatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

# ch.setFormatter(formatter)
sysloghandler.setFormatter(syslogformatter)

# logger.addHandler(ch)
logger.addHandler(sysloghandler)

def main():
    logger.debug("ERROR")
    token = sys.argv[1]
    server = DongobotServer.DongobotServer(token, logger)
    server.run()

if __name__ == "__main__":
    main()
