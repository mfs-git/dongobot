# -*- coding: utf-8 -*-

import logging
import DongobotServer

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    server = DongobotServer.DongobotServer('244318883:AAHR70lPzcSIyUXxAi1-9GPXYAjVKcrrzlg')
    server.run()

if __name__ == "__main__":
    main()
