from bots import RequestHandler
from models import Country
from datetime import datetime
from mongoengine import connect
from bots.botsExceptions import *


connect("climatemps")


class CountryUrlFinder(RequestHandler):
    def __init__(self, print_errors=False):
        RequestHandler.__init__(self, url="http://www.climatemps.com/",
                                print_errors=print_errors)
        self.urls = []

    @property
    def urls(self):
        return self.__urls

    @urls.setter
    def urls(self, urls):
        self.__urls = urls
        if self._page_request():
            country_table = self._get_xpath("//tr[2]/td/table/tr/td/table[2]")
            for href in country_table.xpath("./tr/td"):
                country_list = href.xpath("./table/tr/td/a/text()")
                url_list = href.xpath("./table/tr/td/a/@href")
                self.urls.extend(zip(country_list, url_list))

    def update_country_urls(self):
        for i in self.urls:
            country_data = {"set__updated_at": datetime.utcnow(),
                            "country": i[0].lower(),
                            "url": i[1]
                            }
            try:
                Country.objects(url=i[1]).update(upsert=True, **country_data)
            except Exception as e:
                error_info = ErrorInfo()
                self._error_log(str(e), error_info.file_name, error_info.line_number)
                if self.print_errors:
                    print("Exception: {}, at line {}, file {}".format(e, error_info.line_number, error_info.file_name))


class CityUrlFinder(RequestHandler):
    def __init__(self, url, print_errors=False):
        RequestHandler.__init__(url=url, print_errors=print_errors)
        

if __name__ == '__main__':
    test_countries = CountryUrlFinder(print_errors=True)
    test_countries.update_country_urls()