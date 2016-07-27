import requests
from lxml import html
from time import sleep
from datetime import datetime
from models import AccessControl, ErrorLog

__author__ = 'João Trevizoli Esteves'


class StatusError(Exception):
    pass


class BadXpath(Exception):
    pass


class BadUrl(Exception):
    pass


class RequestHandler(object):
    """
    Request handler for the site urls

    ..note::
        This objects logs the inaccessible urls automatically to
        the mongo database.

    :param: url: Any url to be requested
    :type: url: unicode or str
    """
    def __init__(self, url):
        self.url = url
        self.data = None
        self.__request_control = False

    def _request_log(self, **kwargs):
        """
        Protected attribute to log the data,
        pass an dict with the data to be logged.

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
            print(e)

    def _error_log(self, exception):
        error_log = {'url': self.url,
                     'created_at': datetime.utcnow(),
                     'exception': exception}
        ErrorLog(**error_log).save()

    def _page_request(self):

        access_tries = 0
        request_log_data = {}
        while access_tries < 3:
            try:
                try:
                    self.data = requests.get(self.url)
                    if self.data.status_code != 200:
                        raise StatusError(u'The server returned an status'
                                          u'code diferent then 200: \n'
                                          u'it was {}'.format(self.data.status_code))
                    access_tries = 3
                    request_log_data["set__status_code"] = 200
                    request_log_data["set__access_success"] = True
                    self._request_log(**request_log_data)
                    self.__request_control = True
                except StatusError:
                    self._error_log('StatusError')
                    request_log_data["set__status_code"] = self.data.status_code
                sleep(2)
            except Exception as e:
                self._error_log(str(e))
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
            self._error_log('BadXpath')
            raise BadXpath(u'This is an invalid Xpath, '
                           u'nothing was found in this node.')