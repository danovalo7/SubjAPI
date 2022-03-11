import pymongo

from SubjAPIDatabase import SubjAPIDatabase
from typing import Optional

from SubjAPIExceptions import NoCredentialsError, NotConnectedError


class SubjAPIMongoDatabase(SubjAPIDatabase):
    def __init__(self, cache_size: int = 10, threaded: Optional[bool] = None, password: Optional[str] = None):
        super().__init__(cache_size, threaded)
        self._encrypted_credentials = b'[REDACTED]'
        self._salt = '[REDACTED]'
        self._connection: Optional[pymongo.MongoClient] = None
        self._collection: Optional[pymongo.collection.Collection] = None
        super().__after_init__(password=password)

    def connect(self, password: Optional[str], other: Optional[str] = None) -> None:
        if password is None and other is None:
            raise NoCredentialsError("No valid credentials found. Enter built-in credential password or pass connection string to other.")
        if password is not None:
            self._connection = pymongo.MongoClient(self.decrypt(password))
        else:
            self._connection = pymongo.MongoClient(other)
        self._connection.autocommit = True
        self._collection = self._connection["subjapidb"]["subjects"]
        self.connected = True

    def get_indexed(self) -> set:
        if not self.connected:
            raise NotConnectedError("Not connected; run <self>.connect() to initialize connection first.")
        return {item["id"] for item in self._collection.find({}, {"id": 1})}

    def _submit(self, cache) -> None:
        if not self.connected:
            raise NotConnectedError("Not connected; run <self>.connect() to initialize connection first.")
        to_update = [pymongo.ReplaceOne({'id': row["id"]}, row, upsert=True) for row in cache]
        self._collection.bulk_write(to_update)

    def _cleanup(self):
        if self._connection is not None:
            self._connection.close()
        self.connected = False
