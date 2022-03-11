from json import JSONDecodeError
from pathlib import Path
from typing import Optional

from google.cloud import datastore

from SubjAPIDatabase import SubjAPIDatabase
from SubjAPIExceptions import *


class SubjAPIGoogleDatabase(SubjAPIDatabase):
    def __init__(self, cache_size: int = 10, threaded: Optional[bool] = None, password: Optional[str] = None):
        super().__init__(cache_size, threaded)
        self._encrypted_credentials = b'[REDACTED]'
        self._salt = '[REDACTED]'
        self._datastore_client: Optional[datastore.Client] = None
        self._partkey: Optional[datastore.Key] = None
        self._datastore_client: Optional[datastore.Client] = None
        super().__after_init__(password=password)

    def connect(self, password: Optional[str], other: Optional[str] = None):
        import json
        from google.oauth2.service_account import Credentials
        self._datastore_client = None
        if password is not None:
            creds = Credentials.from_service_account_info(json.loads(self.decrypt(password)))
            self._datastore_client = datastore.Client(credentials=creds, project=creds.project_id)
        elif other is not None and Path(other).is_file():
            try:
                self._datastore_client = datastore.Client.from_service_account_json(other)
            except JSONDecodeError:
                pass
        if self._datastore_client is None:
            raise NoCredentialsError("No valid credentials found. Enter built-in credential password or add credentials.json to CWD.")
        self._partkey = self._datastore_client.key("subject")
        self.connected = True

    def get_indexed(self):
        if self._datastore_client is None:
            raise NotConnectedError("Run connect() to initialize database connection first.")
        q = self._datastore_client.query()
        q.keys_only()
        return {e.id for e in q.fetch()}

    def _submit(self, cache):
        ents = []
        for item in cache:
            ent = datastore.entity.Entity(self._partkey.completed_key(item.pop("id")))
            ent.update(item)
            ents.append(ent)
        self._datastore_client.put_multi(ents)
