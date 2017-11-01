from spider import *
from models import AccessControl
from mongoengine.connection import disconnect, connect
from threading import Thread
import sys
from queue import LifoQueue
connect("climatemps_test")


class Worker(object):

    def __init__(self, print_errors=False):
        self.print_errors = print_errors

    def __get_countries(self):
        countries = CountryUrlFinder(print_errors=self.print_errors)
        print("The bots are searching for countries...")
        countries.update_country_urls()
        print("Done \o/ !")

    def get_cities(self):
        cities = AccessControl.objects(url_type="country", access_success=False)
        for i in cities:
            print(i.url)
            city_finder = CityUrlFinder(url=i.url,
                                        country=i.country,
                                        print_errors=self.print_errors)
            city_finder.update_normals_urls()
            sys.stdout.write(".")

    def update_normals(self):
        normals = Normals.objects(access_success=False)[:5]
        while normals != 0:
            sys.stdout.write("[")
            for i in normals:
                sys.stdout.write((str(i.url) + ", "))
                sys.stdout.flush()
                normals_finder = NormalsSpider(url=i.url,
                                            print_errors=self.print_errors)
                normals_finder.update_normals_data()
            sys.stdout.flush()
            print("]")
            print("A bulk of {} requests were done \o/".format(len(normals)))
            normals = Normals.objects(access_success=False)[:5]

    def start(self):
        # self.__get_countries()
        # self.get_cities()
        self.update_normals()


class ThreadedNormalWorker(object):
    def __init__(self, print_errors=False):
        self.print_errors = print_errors
        self.queue = LifoQueue()

    def get_url_bulk(self):
        normals = Normals.objects(access_success=False)
        for i in normals:
            self.queue.put(item=i)

    def grab_from_queue(self):
        while not self.queue.empty():
            url = self.queue.get()
            normals_finder = NormalsSpider(url=url.url,
                                           print_errors=self.print_errors)
            normals_finder.update_normals_data()
            print(url.url)
            self.queue.task_done()

    def start(self, n_threads):
        self.get_url_bulk()
        for i in range(n_threads):
            thread = Thread(target=self.grab_from_queue())
            thread.start()
        self.queue.join()

if __name__ == '__main__':
    worker = Worker(print_errors=True)
    worker.start()
    # worker = ThreadedNormalWorker(print_errors=True)
    # worker.start(10)
