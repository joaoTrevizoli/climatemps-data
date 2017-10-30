from collections import deque
from spider import RequestHandler
from models import Normals, AccessControl
from datetime import datetime
from spider.botsExceptions import *
from LatLon23 import string2latlon
from slugify import slugify

import warnings
import re

from mongoengine import connect
connect("climatemps_test")


def parse_date_time(date_string):
    date_string = date_string.replace(":", " ")
    date_string = date_string.replace("'", "")
    date_string = date_string.replace("h", "")
    return datetime.strptime(date_string, "%H %M")


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
            access_control_data = {"set__updated_at": datetime.utcnow(),
                                   "set__access_success": False,
                                   "set__status_code": None,
                                   "set__url_type": "country",
                                   "country": i[0].lower(),
                                   "url": i[1]}
            try:
                AccessControl.objects(url=i[1]).update(upsert=True, **access_control_data)
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
            try:
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
                    try:
                        lat_lon = (string2latlon(contents[1], contents[2], "d%°%m%'%h"))
                        contents[1], contents[2] = lat_lon.lon.decimal_degree, lat_lon.lat.decimal_degree
                    except:
                        raise BadXpath("wrong path")
                    try:
                        contents[3] = float(contents[3])
                    except:
                        contents[3] = None
                    content_dict = {"url": normal_url,
                                    "country": self.country,
                                    "city": contents[0],
                                    "point": contents[1:3],
                                    "altitude": contents[3],
                                    "climate": contents[4],
                                    "biome": contents[5]}

                    self.city_data.append(content_dict)
            except BadXpath:
                try:
                    data_ul = self._get_xpath("//ul")
                    geo_data = data_ul.xpath("./li[1]/text()|./li[1]/a/text()")[0]
                    geo_data = geo_data.split(",", 1)

                    point = re.findall(r"\d+°\d+'\S{1}", geo_data[1])
                    lat_lon = (string2latlon(point[0], point[1], "d%°%m%'%h"))

                    city = geo_data[0]
                    point = [lat_lon.lon.decimal_degree, lat_lon.lat.decimal_degree]
                    altitude = float(re.findall(r"(\d+)\s+?m\s+?.*?\(-?\d+ ft\)", geo_data[1])[0])
                    classification = data_ul.xpath("./li[2]/text()|./li[2]/b/text()")
                    classification = "".join(classification)

                    try:
                        biome = re.findall(r"has a (.*) climate \(", classification)[0].lower()
                    except:
                        biome = None

                    climate = re.findall(r"-Geiger classification: (\w+)\)", classification)[0].lower()

                    content_dict = {"url": self.url,
                                    "country": self.country,
                                    "city": city.lower(),
                                    "point": point,
                                    "altitude": altitude,
                                    "climate": climate,
                                    "biome": biome}
                    self.city_data.append(content_dict)

                    warnings.warn("This may be as city url", UserWarning)
                except:
                    self._error_log("BadXpath", "url_spider", 131)
                    print("Impossible to get the data")

    def update_normals_urls(self):
        for i in self.city_data:
            normal_data = {"set__updated_at": datetime.utcnow(),
                           "set__access_success": False,
                           }
            access_control_data = {"set__updated_at": datetime.utcnow(),
                                   "set__access_success": True,
                                   "set__status_code": None,
                                   "url_type": "normal",
                                   "url": i["url"]}
            try:
                normal_data.update(i)
                Normals.objects(url=normal_data["url"]).update(new=True, upsert=True, **normal_data)
                AccessControl.objects(url=access_control_data["url"]).update(upsert=True, **access_control_data)
            except Exception as e:
                print(access_control_data)
                print(e)
                error_info = ErrorInfo()
                self._error_log(str(e), error_info.file_name, error_info.line_number)
                if self.print_errors:
                    print("Exception: {}, at line {}, file {}".format(e, error_info.line_number, error_info.file_name))


class NormalsSpider(RequestHandler):

    def __init__(self, url, print_errors):
        RequestHandler.__init__(self, url, print_errors)
        self.normal_data = {}

    def get_normal_urls(self):
        try:
            if self._page_request():
                hrefs = self._get_xpath("//table[@id='background-image']|//div[@class='table']/table/tbody")
                return list(set(hrefs.xpath("./tr/td/a/@href")))

        except Exception as e:
                print(e)
    @property
    def normal_data(self):
        return self.__normal_data

    @normal_data.setter
    def normal_data(self, normal_data):
        self.__normal_data = normal_data
        base_url = self.url
        urls = ["{}{}".format(base_url, i) for i in self.get_normal_urls()]
        print(urls)
        for i in urls:
            self.url = i

            try:
                if self._page_request():
                    normal_table = self._get_xpath("//table[@class='countrytable']")
                    months = normal_table.xpath("./thead/tr/th[@class='countrytable']/a/text()|"
                                                "./thead/tr/th[@scope='col']/a/text()")
                    # normal_table = self._get_xpath("//table[@id='background-image']|//div[@class='table']/table")
                    # months = normal_table.xpath("./thead/tr/th[@class='countrytable']/a/text()|"
                    #                             "./thead/tr/th[@scope='col']/a/text()")

                    january_index = months.index("Jan")
                    months = deque(months, maxlen=12)
                    months.rotate(january_index)
                    for i in normal_table.xpath("./tbody/tr"):
                        try:
                            variable_name = i.xpath("./td[@class='countrytable']/div/@alt|./td[@class='countrytable']/img/@alt")[0]
                            variable_name = variable_name.replace(" icon", "")
                            data_list = i.xpath("./td[@class='countrytable']/text()")[:-1]
                            print(data_list)
                            data_list = list(filter(lambda item: item != ' ', data_list))
                            data_list = deque([re.sub(r' \(-?\d+(.\d+|)\)', '', j) for j in data_list], 12)
                            data_list.rotate(january_index)
                            print(data_list)
                            data_list = [parse_date_time(j) if re.match(r'(\d+h \d+\')|(\d+:\d+)', j)
                                         else float(j.replace("-", "0")) for j in data_list]
                        except Exception:
                            pass
                        variable_name = slugify(variable_name, word_boundary=True, separator="_")
                        self.__normal_data[variable_name] = data_list

            except Exception as e:
                error_info = ErrorInfo()
                self._error_log(str(e), error_info.file_name, error_info.line_number)
                if self.print_errors:
                    print("Exception: {}, at line {}, file {}".format(e, error_info.line_number, error_info.file_name))
        self.url = base_url

    def update_normals_data(self):
        normal_data = {"set__updated_at": datetime.utcnow(),
                       "set__new": False,
                       "set__access_success": True
                       }

        try:
            self.normal_data.update(normal_data)
            Normals.objects(url=self.url).update(**self.normal_data)

        except Exception as e:
            error_info = ErrorInfo()
            self._error_log(str(e), error_info.file_name, error_info.line_number)
            if self.print_errors:
                print("Exception: {}, at line {}, file {}".format(e, error_info.line_number, error_info.file_name))


# if __name__ == '__main__':
#     test_countries = CountryUrlFinder(print_errors=True)
#     test_countries.update_country_urls()
#
#     test_city_url = CityUrlFinder(url="http://www.equatorial-guinea.climatemps.com/", country="Equatorial-Guinea", print_errors=True)
#     print(test_city_url.city_data)
#     test_normals_spider = NormalsSpider(url="http://www.kabompo.climatemps.com/", print_errors=True)
#     print(test_normals_spider.update_normals_data())

    teste = "29.2 (84.6)"
    teste2 = "29.2 (84)"