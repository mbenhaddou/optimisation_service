from datetime import datetime

from sqlalchemy.dialects.mysql import MEDIUMTEXT

from db.BinaryUUID import BinaryUUID
from db.base_class import Base
from sqlalchemy import Column, DateTime, Text
import uuid


class SolutionRouting(Base):
    uuid = Column(BinaryUUID, primary_key=True, index=True, default=uuid.uuid4)
    creation_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    update_date = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    optimization_request = Column(MEDIUMTEXT)
    optimization_response = Column(MEDIUMTEXT)
    status = Column(Text, index=True)
    status_msg = Column(Text)
    parameters = Column(Text)


