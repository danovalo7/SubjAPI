from typing import Optional, List
from psycopg2 import connect
from psycopg2.extensions import connection, cursor, AsIs
from psycopg2.extras import execute_batch

from SubjAPIDatabase import SubjAPIDatabase
from SubjAPIExceptions import NoCredentialsError, NotConnectedError


class SubjAPIPostgresDatabase(SubjAPIDatabase):
    def __init__(self, cache_size: int = 10, threaded: Optional[bool] = None, password: Optional[str] = None):
        super().__init__(cache_size, threaded)
        self._encrypted_credentials = b'[REDACTED]'
        self._salt = '[REDACTED]'
        self._connection: Optional[connection] = None
        self._cursor: Optional[cursor] = None
        self._columns = 'id', 'exists', 'url', 'date_indexed', 'code', 'name', 'short', 'credits', 'students_evaluated', 'average_grade', 'description_length', 'date_modified'
        super().__after_init__(password=password)

    def connect(self, password: Optional[str], other: Optional[str] = None) -> None:
        if password is None and other is None:
            raise NoCredentialsError("No valid credentials found. Enter built-in credential password or pass connection string to other.")
        if password is not None:
            self._connection = connect(self.decrypt(password))
        else:
            self._connection = connect(other)
        self._connection.autocommit = True
        self._cursor = self._connection.cursor()
        self._cursor.execute("PREPARE subjapi_stmt AS INSERT INTO subjects (%s) VALUES (" + ','.join(['$' + str(i + 1) for i in range(len(self._columns))]) + ");",
                             vars=(AsIs(','.join(self._columns)),))
        self.connected = True

    def get_indexed(self) -> set:
        if self._cursor is None:
            raise NotConnectedError("No cursor; ")
        self._cursor.execute("SELECT id FROM subjects;")
        return {row[0] for row in self._cursor.fetchall()}

    def _submit(self, cache: List[dict]) -> None:
        if self._cursor is None:
            raise NotConnectedError("No cursor; run <self>.connect() to initialize connection first.")
        mod_cache = [tuple([subject.get(column) for column in self._columns]) for subject in cache]
        execute_batch(cur=self._cursor, sql="EXECUTE subjapi_stmt (" + ', '.join(['%s'] * len(self._columns)) + ");", argslist=mod_cache)

    def _cleanup(self):
        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        self.connected = False
