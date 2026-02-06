from datetime import datetime

from db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, DateTime, String, LargeBinary, Float, VARCHAR, BINARY, Text
import uuid
from db.BinaryUUID import BinaryUUID

class GeoEntries(Base):
    uuid = Column(BinaryUUID, primary_key=True, index=True, default=uuid.uuid4)
    creation_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    update_date = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    key = Column(VARCHAR(255), unique=True, index=True)
    val = Column(Text)
    exp = Column(Float)