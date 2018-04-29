# -*- coding: utf-8 -*-
import logging


def config(logger_output_filepath):
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=logger_output_filepath,
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    # Now, we can log to the root logger, or any other logger. First the root...
    # logging.info('Jackdaws love my big sphinx of quartz.'

    # # Now, define a couple of other loggers which might represent areas in your
    # # application:
    #
    # logger1 = logging.getLogger('myapp.area1')
    # logger2 = logging.getLogger('myapp.area2')
    #
    # logger1.debug('Quick zephyrs blow, vexing daft Jim.') # Won't print, file only
    # logger1.info('How quickly daft jumping zebras vex.') # Printed and to file
    # logger2.warning('Jail zesty vixen who grabbed pay from quack.') # Printed and to file
    # logger2.error('The five boxing wizards jump quickly.') # Printed and to file.


def print(msg, *args, **kwargs):
    logging.debug(msg, *args, **kwargs)
