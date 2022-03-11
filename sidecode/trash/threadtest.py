from concurrent.futures import wait, ThreadPoolExecutor, FIRST_COMPLETED
from pprint import pprint
from signal import SIGINT, SIGTERM, signal
from sys import exit
from time import sleep, perf_counter
from typing import Callable

from bs4 import BeautifulSoup
from requests import get as get_request
from requests.exceptions import SSLError


class SubjAPI:
    grade_dict = {0: "X", 1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}
    url_head = "://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod="
    url_tail = "&lng=sk"
    max_connections = 3

    def __init__(self, print_f: Callable = lambda *args: None):
        self.tcache = []
        self.protocol = "https"
        try:
            get_request("https://vzdelavanie.uniza.sk/")
        except SSLError:
            print_f("! CRITWARN : SSL error - falling back to http.")
            self.protocol = "http"
            get_request("http://vzdelavanie.uniza.sk/")  # in case the site is fully dead, let it raise an error
        signal(SIGINT, self.exit_cleanup)
        signal(SIGTERM, self.exit_cleanup)
        self.print_f = print_f

    def fetch(self, subject_id: int):
        url = self.url_head + str(subject_id) + self.url_tail
        r = get_request(self.protocol + url)
        soup = BeautifulSoup(r.text, 'html.parser')
        charset = soup.head.meta.attrs['content'][soup.head.meta.attrs['content'].index('charset=') + 8:]
        r.encoding = charset
        self.tcache.append(BeautifulSoup(r.text, 'html.parser').table.find_all("td")[3].text[16:].strip())

    def fetch_threaded(self, start: int, end: int):
        self.print_f("Fetching with ", self.max_connections, " simultaneous connections.")
        t0 = perf_counter()
        with ThreadPoolExecutor(max_workers=self.max_connections) as tpe:
            id_generator = iter(range(start, end))
            future_set = set()
            for _ in range(self.max_connections):
                try:
                    future_set.add(tpe.submit(self.fetch, next(id_generator)))
                except StopIteration:
                    break
            while True:
                next_id = next(id_generator, None)
                if next_id is None:
                    break
                done, not_done = tuple(wait(future_set, return_when=FIRST_COMPLETED))
                future_set -= done
                future_set.add(tpe.submit(self.fetch, next_id))
        wait(future_set)
        t1 = perf_counter()
        print("Done, took ", t1 - t0, " seconds.")
        retcache = self.tcache
        self.tcache = []
        return retcache

    # noinspection PyUnusedLocal
    def exit_cleanup(self, signum, frame):

        self.print_f("Done. Operation interrupted, total ", len(self.tcache), " subjects added to database.")
        sleep(1.5)
        exit(0)


if __name__ == "__main__":
    subjapi = SubjAPI(print_f=print)
    res = {}
    for mc in range(1, 21):
        subjapi.max_connections = mc
        res[mc] = subjapi.fetch_threaded(start=30, end=50)
    pprint(res)
