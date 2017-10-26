import requests
from lxml import html
from time import sleep
from datetime import datetime
from models import AccessControl, ErrorLog
from spider.botsExceptions import *


__author__ = 'João Trevizoli Esteves'


class RequestHandler(object):
    """
    Request handler for the site urls

    ..note::
        This objects logs the inaccessible urls automatically to
        the mongo database.

    :param: url: Any url to be requested
    :type: url: unicode or str
    """
    def __init__(self, url, print_errors=False):
        self.url = url
        self.print_errors = print_errors
        self.data = None
        self.__request_control = False
        self.__header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                                       'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 '
                                       'Safari/537.36'}

    def _request_log(self, **kwargs):
        """
        Protected attribute to log the the historic of requests
        done by the class, pass an dict with the data to be logged.

        :param kwargs:
        :return: None
        """
        request_log_data = {"set__updated_at": datetime.utcnow(),
                            "set__access_success": False,
                            "set__status_code": None,
                            }
        request_log_data.update(kwargs)
        try:
            if 'set__url' in request_log_data:
                AccessControl.objects(url=request_log_data['set__url']).update(new=True, upsert=True, **request_log_data)
            else:
                AccessControl.objects(url=self.url).update(new=True, upsert=True, **request_log_data)
        except Exception as e:
            error_info = ErrorInfo()
            self._error_log(str(e), error_info.file_name, error_info.line_number)
            if self.print_errors:
                print("Exception: {}, at line {}, file {}".format(e, error_info.line_number, error_info.file_name))

    def _error_log(self, exception, file_name, line_number):
        error_log = {'url': self.url,
                     'created_at': datetime.utcnow(),
                     'exception': exception,
                     'file_name': file_name,
                     'line_number': line_number}
        ErrorLog(**error_log).save()

    def _page_request(self):

        access_tries = 0
        request_log_data = {}
        while access_tries < 5:
            try:
                try:
                    self.data = requests.get(self.url, headers=self.__header)
                    print(self.data)
                    if self.data.status_code != 200:
                        raise StatusError(u'The server returned an status'
                                          u'code diferent then 200: \n'
                                          u'it was {}'.format(self.data.status_code))
                    access_tries = 5
                    request_log_data["set__status_code"] = 200
                    request_log_data["set__access_success"] = True
                    request_log_data["set__content"] = self.data.text
                    self._request_log(**request_log_data)
                    self.__request_control = True
                except StatusError:
                    error_info = ErrorInfo()
                    self._error_log('StatusError', error_info.file_name, error_info.line_number)
                    request_log_data["set__status_code"] = self.data.status_code
                    if self.print_errors:
                        print("StatusError: {}".format(self.data.status_code))
                sleep(3)
            except Exception as e:
                error_info = ErrorInfo()
                self._error_log(str(e), error_info.file_name, error_info.line_number)
                if self.print_errors:
                    print("Exception: {}, at line {}, file {}".format(e, error_info.line_number, error_info.file_name))
            access_tries += 1

        if self.__request_control:
            return True
        return False

    def _get_xpath(self, xpath):
        """
        Returns data inside path
        """
        try:
            return html.fromstring(self.data.text).xpath(xpath)[0]
        except:
            error_info = ErrorInfo()
            self._error_log('BadXpath', error_info.file_name, error_info.line_number)
            raise BadXpath(u'This is an invalid Xpath, '
                           u'nothing was found in this node.')