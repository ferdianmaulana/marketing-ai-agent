from sqlalchemy import create_engine, Column, String, BigInteger, Integer, DateTime, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

JAKARTA_TZ = timezone(timedelta(hours=7))  # WIB, no DST

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ChannelSnapshot(Base):
    __tablename__ = "channel_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(64), nullable=False, index=True)
    channel_name = Column(String(256))
    subscriber_count = Column(BigInteger)
    view_count = Column(BigInteger)
    video_count = Column(Integer)
    fetched_at = Column(DateTime, default=lambda: datetime.now(JAKARTA_TZ))


class VideoStats(Base):
    __tablename__ = "video_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(64), nullable=False, index=True)
    video_url = Column(String(256))
    channel_id = Column(String(64), nullable=False, index=True)
    channel_name = Column(String(256))
    title = Column(Text)
    published_at = Column(DateTime)
    view_count = Column(BigInteger)
    like_count = Column(BigInteger)
    comment_count = Column(BigInteger)
    duration_seconds = Column(Integer)
    engagement_rate = Column(Float)   # (likes + comments) / views * 100
    fetched_at = Column(DateTime, default=lambda: datetime.now(JAKARTA_TZ))


def init_db():
    Base.metadata.create_all(engine)
    print("Database tables created.")


if __name__ == "__main__":
    init_db()
