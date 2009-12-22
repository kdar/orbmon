import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='.orbmon.error.log',
                    filemode='w')

log = logging.getLogger('logger')
