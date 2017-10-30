from spider import RequestHandler
from mongoengine import connect
from spider import *
connect("climatemps_test")

if __name__ == '__main__':
    test_normals_spider = NormalsSpider(url="http://www.fortaleza.climatemps.com/", print_errors=True)
    print(test_normals_spider.normal_data)