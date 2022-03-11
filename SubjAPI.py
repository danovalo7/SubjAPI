from concurrent.futures import ThreadPoolExecutor, wait as wait_for_future, FIRST_COMPLETED
from datetime import datetime
from getpass import getpass
from signal import SIGINT, SIGTERM, signal
from sys import exit
from threading import Lock
from time import perf_counter, sleep
from typing import Callable, Optional

from bs4 import BeautifulSoup
from requests import get as get_request
from requests.exceptions import SSLError

from SubjAPIDatabase import SubjAPIDatabase
from SubjAPIExceptions import NotConnectedError, IncorrectPasswordError


class SubjAPI:
    """Main class of the SubjAPI project. Connects to the Uniza website, downloads info about subjects,
    and stores it in a database. Supports multithreading, and outputs progress info.
    NOTE: code written before fstrings existed, and +ing was simpler than formatting, so prints look weird."""
    grade_dict = {0: "X", 1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}
    url_head = "://vzdelavanie.uniza.sk/vzdelavanie/planinfo.php?kod="
    url_tail = "&lng=sk"
    max_connections = 10
    update = False

    def __init__(self, database: SubjAPIDatabase, password: Optional[str] = None,
                 print_f: Callable = lambda *args, **kwargs: None):
        if not database.connected and password is None:
            raise NotConnectedError("Database not connected and no password supplied.")
        if not database.connected:
            database.connect(password)
        self.database = database
        self._future_set = set()
        self._cache_lock = Lock()
        self._print_lock = Lock()
        self.print_f = print_f
        self.protocol = "https"
        try:
            get_request("https://vzdelavanie.uniza.sk/")
        except SSLError:
            print("! CRITWARN : SSL error - falling back to http.")
            self.protocol = "http"
            get_request("http://vzdelavanie.uniza.sk/")  # in case the site is fully dead, let it raise an error
        # noinspection PyTypeChecker
        signal(SIGINT, self.exit_cleanup)
        # noinspection PyTypeChecker
        signal(SIGTERM, self.exit_cleanup)
        self.indexed_subject_id_list = database.get_indexed()
        self.fetched = 0
        self.empty_fetched = 0
        self.skipped = 0
        self.processed_since_last = 0
        self.starting_time = 0

    def update_indexed(self):
        self.indexed_subject_id_list = self.database.get_indexed()

    def fetch(self, subject_id: int) -> int:
        def extract_parenthesis(s: str):
            y = s.rfind(")")
            x = s[:y].rfind("(")
            if x != -1 and y != -1 and x + 1 < y:
                return s[x + 1:y]

        if not self.update and subject_id in self.indexed_subject_id_list:
            with self._cache_lock:
                self.skipped += 1
                self.processed_since_last += 1
            return 0
        url = self.url_head + str(subject_id) + self.url_tail
        r = get_request(self.protocol + url)
        soup = BeautifulSoup(r.text, 'html.parser')
        charset = soup.head.meta.attrs['content'][soup.head.meta.attrs['content'].index('charset=') + 8:]
        r.encoding = charset
        soup = BeautifulSoup(r.text, 'html.parser')
        if soup.table is None:
            subj = {"id": subject_id, "exists": False, "url": "https" + url, "date_indexed": datetime.now()}
            with self._print_lock:
                self.print_f(str(subj["id"]) + ": EMPTY; ", end="")
            with self._cache_lock:
                self.database.cache(subj)
                self.empty_fetched += 1
                self.processed_since_last += 1
            return 1
        subj = {}
        td = soup.table.find_all("td")
        subj["id"] = subject_id
        subj["exists"] = True
        subj["code"] = td[2].text[14:].strip()
        subj["name"] = td[3].text[16:].strip()
        subj["short"] = extract_parenthesis(subj["name"]).strip()
        subj["url"] = "https" + url
        try:
            subj["credits"] = float(td[5].text[td[5].text.rfind(" ") + 1:])
        except ValueError:
            subj["credits"] = None
        try:
            subj["students_evaluated"] = int(td[15].text[td[15].text.rfind(" ") + 1:])
        except ValueError:
            subj["students_evaluated"] = None
        try:
            subj["average_grade"] = self.grade_dict[
                round(sum([(n + 1) * float(item.text[:-1].strip()) for n, item in enumerate(td[22:28])]) / 100)]
        except ValueError:
            subj["average_grade"] = None
        try:
            subj["description_length"] = len(td[9].text) + len(td[10].text) + len(td[11].text) + len(td[12].text)
        except ValueError:
            subj["description_length"] = None
        try:
            subj["date_modified"] = datetime(
                *[int(td[29].text[23:].replace(".", " ").replace(":", " ").split(" ")[i]) for i in [2, 1, 0, 3, 4, 5]])
        except (ValueError, IndexError):
            subj["date_modified"] = None
        subj["date_indexed"] = datetime.now()
        with self._print_lock:
            self.print_f(str(subj["id"]) + ": " + subj["code"] + "; ", end="")
        with self._cache_lock:
            self.database.cache(subj)
            self.fetched += 1
            self.processed_since_last += 1
        return 2

    def fetch_range(self, start: int, end: int, print_every: int = 0):
        self.starting_time = perf_counter()
        end += 1
        with self._print_lock:
            self.print_f("Fetching with ", self.max_connections, " simultaneous connections.")

        for i in range(start, end):
            if not self.update and i in self.indexed_subject_id_list:
                self.skipped += 1
                continue
            start = i
            break
        if self.skipped > 0:
            with self._print_lock:
                self.print_f("WARN: Some initial chunks already indexed, skipped. (", self.skipped, ")")

        fetched_before = self.fetched
        empty_fetched_before = self.empty_fetched
        skipped_before = self.skipped
        per_second_before = 0

        with ThreadPoolExecutor(max_workers=self.max_connections) as tpe:
            id_generator = iter(range(start, end))

            for _ in range(self.max_connections):
                next_id = next(id_generator, None)
                if next_id is None:
                    break
                self._future_set.add(tpe.submit(self.fetch, next_id))

            while True:
                if print_every and self.processed_since_last >= print_every:
                    per_second_before = self.print_stats(fb=fetched_before, efb=empty_fetched_before, sb=skipped_before,
                                                         psb=per_second_before)
                    fetched_before = self.fetched
                    empty_fetched_before = self.empty_fetched
                    skipped_before = self.skipped
                    self.processed_since_last -= print_every
                done, not_done = tuple(wait_for_future(self._future_set, return_when=FIRST_COMPLETED))
                self._future_set -= done
                for i in range(2 * self.max_connections - len(self._future_set)):
                    next_id = next(id_generator, None)
                    if next_id is None:
                        break
                    self._future_set.add(tpe.submit(self.fetch, next_id))
                if next_id is None:
                    break

        wait_for_future(self._future_set)
        self._future_set = set()
        self.database.submit(exitting=True)
        self.print_f("\n\nCOMPLETED\n   - all records in range processed.")
        self.print_stats()

    def print_stats(self, fb=None, efb=None, sb=None, psb=None):
        with self._print_lock:
            duration = perf_counter() - self.starting_time
            per_second = round((self.fetched + self.empty_fetched) / duration, 2)
            self.print_f("\n\nStats:")
            self.print_f(" -   processed : ", self.fetched + self.skipped + self.empty_fetched, end=" ")
            if fb is not None and efb is not None and sb is not None:
                self.print_f("(+" + str((self.fetched + self.skipped + self.empty_fetched) - (fb + efb + sb)) + ")",
                             end="")
            self.print_f("\n    └  skipped : ", self.skipped, end=" ")
            if sb is not None:
                self.print_f("(+" + str(self.skipped - sb) + ")", end="")
            self.print_f("\n    └    added : ", self.fetched + self.empty_fetched, end=" ")
            if fb is not None and efb is not None:
                self.print_f("(+" + str((self.fetched + self.empty_fetched) - (fb + efb)) + ")", end="")
            self.print_f("\n       └  full : ", self.fetched, end=" ")
            if fb is not None:
                self.print_f("(+" + str(self.fetched - fb) + ")", end="")
            self.print_f("\n       └ empty : ", self.empty_fetched, end=" ")
            if efb is not None:
                self.print_f("(+" + str(self.empty_fetched - efb) + ")", end="")
            self.print_f("\n -  time taken : ", round(duration, 2))
            self.print_f(" -     added/s : ", per_second, end=" ")
            if psb is not None:
                self.print_f(
                    "(" + {True: "-", False: "+"}[per_second < psb] + str(round(abs(per_second - psb), 2)) + ")")
            self.print_f()
        return per_second

    # noinspection PyUnusedLocal
    def exit_cleanup(self, *args, **kwargs):
        with self._print_lock:
            self.print_f("\nWARN: Interrupt recieved. \nSubmitting leftovers and exitting...")
        wait_for_future(self._future_set)
        self._future_set = set()
        self.database.submit(exitting=True)
        self.print_stats()
        sleep(1.5)
        exit(0)


if __name__ == "__main__":
    from SubjAPIMongoDatabase import SubjAPIMongoDatabase
    from sys import stdout


    def autoflush_print(*args, **kwargs):
        print(*args, **kwargs)
        stdout.flush()


    subjapi: Optional[SubjAPI] = None
    while subjapi is None:
        try:
            subjapi = SubjAPI(SubjAPIMongoDatabase(password=getpass(), threaded=True), print_f=autoflush_print)
        except IncorrectPasswordError:
            pass
    subjapi.update = True
    subjapi.fetch_range(start=1, end=300000, print_every=50)
