from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class OptionIVHistory(Base):
    __tablename__ = 'iv_history'
    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    expiry = Column(String, nullable=False)
    strike = Column(Float, nullable=False)
    option_type = Column(String, nullable=False)
    iv = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

DATABASE_URL = 'postgresql://user:password@localhost:5432/black_scholes'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_iv_db():
    Base.metadata.create_all(engine) 