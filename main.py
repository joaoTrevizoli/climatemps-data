from bots import RequestHandler
from mongoengine import connect

connect("climatemps")

if __name__ == '__main__':
    base_url = "http://www.climatemps.com/"
    requester = RequestHandler(base_url)
    print(requester.data)
