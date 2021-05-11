import os
import sys
import logging
import pathlib

from datetime import datetime
import tkinter as tk

loggers = {}

class GuiHandler(logging.StreamHandler):
    '''
    Extention of a logging.StreamHandler to print message on a 
    tkinter Text widget

    HISTORY
    -------
    2020 11 05, Stefano Rapisarda (Uppsala), creation date
        I made a modified version of StreamHandler adding few
        lines to the native emit method. Now logging messages
        can also be printed on a tkinter text widget! Nice
    '''

    def __init__(self, text_widget=None, *args, **kwargs):
        logging.StreamHandler.__init__(self,*args,**kwargs)

        self._text_widget = text_widget

    def emit(self, record):
        """
        Emit a record.
        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            msg = self.format(record)
            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            stream.write(msg + self.terminator)
            self.flush()

            # Added by Stefano
            if not self._text_widget is None:
                self._text_widget.insert(tk.END, msg+'\n')
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

def initialize_logger(log_name=False,level=logging.INFO,text_widget=None):
    '''
    Initialize logging options to pring log messages on the screen
    and on a file (if log_name is specified)

    HISTORY
    -------
    unknown   , Stefano Rapisarda (SHAO), creation date
    2020 09 23, Stefano Rapisarda (Uppsala), efficiency improved
    2020 11 06, Stefano Rapisarda (Uppsala), efficiency improved
    '''

    # Creating an instance of the object logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Setting a format for the log
    formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')

    if log_name:
        logging.basicConfig(level=level,
                            format='%(levelname)s: %(asctime)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=log_name.with_suffix('.log'),
                            filemode='w')

    # Creating the log handler
    #handler = logging.StreamHandler(stream=sys.stderr)
    handler = GuiHandler(stream=sys.stderr,text_widget=text_widget)
    handler.setLevel(level)
    handler.setFormatter(formatter) 

    # Configuring the logger with the handler
    logger.addHandler(handler)   

    #if log_name:
        
    #    handler = logging.FileHandler(log_name,"w", encoding=None, delay="true")
    #    handler.setLevel(logging.DEBUG)
    #    handler.setFormatter(formatter)
    #    logger.addHandler(handler)

    return logger

def make_logger(log_name,outdir=pathlib.Path.cwd(),log_widget=None):
    '''
    It creates a logger using the process name and the current date
    and time. It also creates a logs folder inside destination.
    Returns the logger name

    HISTORY
    -------
    2021 02 03, Stefano Rapisarda (Uppsala), creation date
    2021 04 24, Stefano Rapisarda (Uppsala)
        Added global variable loggers to avoid double loggers
    '''

    global loggers

    if type(outdir) == str: outdir = pathlib.Path(outdir)
    log_dir = outdir/'logs'
    if not log_dir.is_dir():
        print('Creating log folder...')
        os.mkdir(log_dir)

    full_log_name = log_dir/log_name

    if loggers.get(log_name):
        return loggers.get(log_name)
    else:
        logger = initialize_logger(full_log_name, text_widget=log_widget)
        loggers[log_name] = logger

    return log_name

def get_logger_name(process_name):
    '''
    Attache date to process_name
    '''
    now = datetime.now()
    date = ('%d_%d_%d') % (now.day,now.month,now.year)
    time = ('%d_%d') % (now.hour,now.minute)

    log_name = '{}_D{}_T{}'.format(process_name,date,time)

    return log_name