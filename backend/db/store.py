
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
import datetime
import json

Base = declarative_base()
Session = None

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    source = Column(String(50), index=True)
    external_id = Column(String(200), index=True, unique=False)
    username = Column(String(200))
    content = Column(Text)
    cleaned_content = Column(Text)
    date = Column(String(50))
    url = Column(Text)
    sentiment = Column(JSON)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

def init_db(db_url: str):
    global Session
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session

def upsert_feedback(session, item: dict):
    """
    Simple insert; if same external_id+source exists, skip.
    """
    exists = session.query(Feedback).filter_by(source=item["source"], external_id=item["external_id"]).first()
    if exists:
        return False
    fb = Feedback(
        source=item["source"],
        external_id=item["external_id"],
        username=item.get("username"),
        content=item.get("content"),
        cleaned_content=item.get("cleaned_content"),
        date=item.get("date"),
        url=item.get("url"),
        sentiment=item.get("sentiment")
    )
    session.add(fb)
    return True
