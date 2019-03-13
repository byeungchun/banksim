import logging, os, sys
from logging.handlers import RotatingFileHandler

cur_dir = os.path.abspath(os.curdir)
sys.path.append(cur_dir)
PROJECT_HOME = cur_dir

def get_logger(name):
    """
    :param name:
    :return:
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    rotate_handler = RotatingFileHandler(PROJECT_HOME + "/" + name + ".log", 'a', 1024*1024*5, 5)
    formatter = logging.Formatter('[%(levelname)s]-%(asctime)s-%(filename)s:%(lineno)s:%(message)s', datefmt="%m%d %H:%M:%S")
    rotate_handler.setFormatter(formatter)
    logger.addHandler(rotate_handler)
    return logger
