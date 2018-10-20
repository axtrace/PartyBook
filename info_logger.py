from datetime import datetime as dt
import logging


class BotLogger(object):
    """ Logs with now time and join all input parameters"""

    def __init__(self, level2=logging.INFO):
        logging.basicConfig(filename="log.txt",
                            format=u'%(levelname)-8s [%(asctime)s]  %(message)s',
                            level=logging.INFO)

    def _join_args(self, *args):
        tmp_list = []
        tmp_list.extend(args)
        return ' '.join(map(str, tmp_list))

    def info(self, *args):
        log_issue = self._join_args(args)
        logging.info(log_issue)

    def error(self, *args):
        log_issue = self._join_args(args)
        logging.error(log_issue)
