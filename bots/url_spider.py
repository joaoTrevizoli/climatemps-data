from bots import RequestHandler
from models import Country, Normals
from datetime import datetime
from mongoengine import connect
from bots.botsExceptions import *
import re
from LatLon23 import string2latlon

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
    def __init__(self, url, country, print_errors=False):
        RequestHandler.__init__(self, url, print_errors)
        self.country = country.lower()
        self.city_data = []

    @property
    def city_data(self):
        return self.__city_data

    @city_data.setter
    def city_data(self, city_data):
        self.__city_data = city_data
        if self._page_request():
            city_data_table = self._get_xpath("//table[@id='background-image']/tbody")
            for tr in city_data_table:
                try:
                    contents = [re.sub(r' \(\d+\)', '', str(i.lower()))
                                for i in tr.xpath("./td/text()|./td/a/text()")[:-2]]
                    normal_url = str(tr.xpath("./td/a/@href")[0])
                except Exception as e:
                    error_info = ErrorInfo()
                    self._error_log('BadXpath', error_info.file_name, error_info.line_number)
                    if self.print_errors:
                        print("Exception: {}, at line {}, file {}".format(e, error_info.line_number,
                                                                          error_info.file_name))
                    raise BadXpath(u'The page structure probably '
                                   u'has changed, please verify the source html.')
                lat_lon = (string2latlon(contents[1], contents[2], "d%°%m%'%h"))
                contents[1], contents[2] = lat_lon.lat.decimal_degree, lat_lon.lon.decimal_degree
                contents[3] = float(contents[3])
                content_dict = {"url": normal_url,
                                "country": self.country,
                                "city": contents[0],
                                "point": contents[1:3],
                                "altitude": contents[3],
                                "climate": contents[4],
                                "biome": contents[5]}

                self.city_data.append(content_dict)

    def update_normals_urls(self):
        for i in self.city_data:
            normal_data = {"set__updated_at": datetime.utcnow(),
                           "set__access_success": False,
                           }
            try:
                normal_data.update(i)
                Normals.objects(url=normal_data["url"]).update(new=True, upsert=True, **normal_data)

            except Exception as e:
                error_info = ErrorInfo()
                self._error_log(str(e), error_info.file_name, error_info.line_number)
                if self.print_errors:
                    print("Exception: {}, at line {}, file {}".format(e, error_info.line_number, error_info.file_name))


class NormalsSpider(RequestHandler):
    def __init__(self, url, print_errors):
        RequestHandler.__init__(self, url, print_errors)
        self.normal_data = {}

    @property
    def normal_data(self):
        return self.__normal_data

    @normal_data.setter
    def normal_data(self, normal_data):
        self.__normal_data = normal_data
        if self._page_request():
            # normal_table = self._get_xpath("//div[@class='table']/table/thead/tr")
            normal_table = self._get_xpath("//div[@class='table']/table")
            months = normal_table.xpath("./thead/tr/th[@class='countrytable']/a/text()")

            for i in normal_table.xpath("./tbody/tr"):
                data_list = i.xpath("./td[@class='countrytable']/text()")[:-1]
                data_list = list(filter(lambda item: item != ' ', data_list))
                data_list = [re.sub(r' \(\d+\)', '', i) for i in data_list]
                print(list(zip(months, data_list)))

if __name__ == '__main__':
    # test_countries = CountryUrlFinder(print_errors=True)
    # test_countries.update_country_urls()

    # test_city_url = CityUrlFinder(url="http://www.brazil.climatemps.com/", country="brazil", print_errors=True)
    # print(test_city_url.update_normals_urls())
    test_normals_spider = NormalsSpider(url="http://www.sete-lagoas.climatemps.com/", print_errors=True)
    print(test_normals_spider.normal_data)