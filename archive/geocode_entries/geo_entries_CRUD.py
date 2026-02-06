import hashlib
import json
import string
from pickle import dumps, loads
from time import time
from typing import Optional

from sqlalchemy.orm import Session

from geocode_entries.geo_entries_model import GeoEntries


class GeoEntriesCRUD:

    def get(self,   db_session: Session,key: str) -> dict:
        query = db_session.query(GeoEntries)
        query = query.filter(GeoEntries.key == key)
        try:
            obj_out=query.first()
            if obj_out:
                return json.loads(obj_out.val)
            else:
                return None
        except:
            return None


    def remove(self, db_session: Session, key: str) -> GeoEntries:
        obj = db_session.query(GeoEntries).get(key)
        db_session.delete(obj)
        db_session.commit()
        return

    def create(self,  db_session: Session,key, value, timeout=None) -> GeoEntries:
        # if no timeout is specified, then we will
        # leave it as a non-expiring value. Other-
        # wise, we add the timeout in seconds to
        # the current time
        try:
            expire = 0 if not timeout else time() + timeout
            # serialize the value with protocol 2
            # ref: https://docs.python.org/2/library/pickle.html#data-stream-format
            #data = memoryview(dumps(value, 2))
            data = json.dumps(value)
            db_obj=GeoEntries(key=key,val=data,exp=expire)
            db_session.add(db_obj)
            db_session.commit()
            db_session.refresh(db_obj)
            return db_obj
        except Exception as e:
            return None

    def update(
           self, db_session: Session,  key, value, timeout=None
    ) -> GeoEntries:
        # if no timeout is specified, then we will
        # leave it as a non-expiring value. Other-
        # wise, we add the timeout in seconds to
        # the current time
        expire = 0 if not timeout else time() + timeout
        # serialize the value with protocol 2
        # ref: https://docs.python.org/2/library/pickle.html#data-stream-format
        #data = memoryview(dumps(value, 2))
        data = json.dumps(value)
        db_obj=self.get( db_session, key)
        db_obj.val=data
        db_obj.exp=expire
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def clear(self, db_session: Session):
        query = db_session.query(GeoEntries)
        count = query.delete(synchronize_session=False)
        db_session.commit()
        return count

    def hash_key(self, key:str):
        puntuation=string.punctuation+" "
        hash_object = hashlib.sha256(key.translate(str.maketrans('','', puntuation)).lower().encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig

geo_entries_crud = GeoEntriesCRUD()
