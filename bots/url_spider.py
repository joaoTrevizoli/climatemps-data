from bots import RequestHandler
from mongoengine import connect

connect("climatemps")


class CountryUrlFinder(RequestHandler):
    def __init__(self):
        RequestHandler.__init__(self, url="http://www.climatemps.com/")
        self.urls = self.__get_country_urls()

    def __get_country_urls(self):
        urls = []
        if self._page_request():
            country_table = self._get_xpath("//tr[2]/td/table/tr/td/table[2]")
            for href in country_table.xpath("./tr/td"):
                urls.extend(href.xpath("./table/tr/td/a/@href"))
        return urls

if __name__ == '__main__':
    test_countries = CountryUrlFinder()
    print(test_countries.urls)