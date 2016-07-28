import sys
import os

__author__ = 'João Trevizoli Esteves'


class ErrorInfo(object):
    def __init__(self):
        self.exc_type, self.exc_obj, self.exc_tb = sys.exc_info()
        self.file_name = self.get_file_name()
        self.line_number = self.get_line_number()

    def get_line_number(self):
        return self.exc_tb.tb_lineno

    def get_file_name(self):
        fname = os.path.split(self.exc_tb.tb_frame.f_code.co_filename)[1]
        return fname


class StatusError(Exception):
    pass


class BadXpath(Exception):
    pass


class BadUrl(Exception):
    pass
