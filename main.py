from spider import RequestHandler
from mongoengine import connect
from spider import *
connect("climatemps")

if __name__ == '__main__':
    test_normals_spider = NormalsSpider(url="http://www.visviri.climatemps.com/", print_errors=True)
    print(test_normals_spider.normal_data)