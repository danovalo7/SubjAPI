from typing import List, Optional

from SubjAPIDatabase import SubjAPIDatabase


class SubjAPIBlankTrackerDatabase(SubjAPIDatabase):
    """Simply stores all subjects submitted into lists and shows them at exit;
    for tracking whether the selected range has any actual records in it."""
    def __init__(self, cache_size: int = 10, threaded: Optional[bool] = None, password: Optional[str] = None) -> None:
        super().__init__(cache_size, threaded, password)
        self.empty: List[dict] = []
        self.full: List[dict] = []
        self.connected = True

    def connect(self, password: Optional[str], other: Optional[str] = None) -> None:
        self.connected = True

    def get_indexed(self) -> set:
        return set()

    def _submit(self, cache: List[dict]) -> None:
        for item in cache:
            if item["exists"]:
                self.full.append(item)
            else:
                self.empty.append(item)

    def _cleanup(self):
        print("Full:  " + " ".join([item["id"] for item in self.full]))
        print("Empty: " + " ".join([item["id"] for item in self.empty]))
        print("Total full:  ", len(self.full))
        print("Total empty: ", len(self.empty))

# put this into main to make this work

    # from SubjAPIBlankTrackerDatabase import SubjAPIBlankTrackerDatabase
    # subjapi = SubjAPI(SubjAPIBlankTrackerDatabase(), print_f=autoflush_print)
    # subjapi.fetch_range(start=277500, end=300000, print_every=50)