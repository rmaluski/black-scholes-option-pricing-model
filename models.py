import os
from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class OptionInput(Base):
    __tablename__ = 'inputs'
    id = Column(Integer, primary_key=True)
    S = Column(Float, nullable=False)
    K = Column(Float, nullable=False)
    T = Column(Float, nullable=False)
    r = Column(Float, nullable=False)
    sigma = Column(Float, nullable=False)
    option_type = Column(String, nullable=False)
    purchase_price = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class OptionOutput(Base):
    __tablename__ = 'outputs'
    id = Column(Integer, primary_key=True)
    input_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    pnl_grid = Column(String, nullable=True)  # Store as JSON string if needed
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Example engine setup (update URL as needed)
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine) 