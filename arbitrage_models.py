from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class OptionChain(Base):
    __tablename__ = "option_chains"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    expiration_date = Column(DateTime, index=True)
    strike_price = Column(Float, index=True)
    option_type = Column(String)  # 'call' or 'put'
    
    # Market data from Yahoo Finance
    last_price = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)
    implied_volatility = Column(Float)
    
    # Theoretical Black-Scholes values
    theoretical_price = Column(Float)
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    rho = Column(Float)
    
    # Market conditions at calculation time
    spot_price = Column(Float)
    risk_free_rate = Column(Float)
    time_to_expiry = Column(Float)
    volatility_used = Column(Float)
    
    # Arbitrage detection
    price_variance = Column(Float)  # (market_price - theoretical_price) / theoretical_price
    is_arbitrage_opportunity = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ArbitrageOpportunity(Base):
    __tablename__ = "arbitrage_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    expiration_date = Column(DateTime, index=True)
    strike_price = Column(Float, index=True)
    option_type = Column(String)
    
    # Market vs Theoretical
    market_price = Column(Float)
    theoretical_price = Column(Float)
    variance_percentage = Column(Float)
    
    # Greeks
    delta = Column(Float)
    gamma = Column(Float)
    theta = Column(Float)
    vega = Column(Float)
    rho = Column(Float)
    
    # Market conditions
    spot_price = Column(Float)
    implied_volatility = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)
    
    # Strategy recommendation
    recommendation = Column(String)  # 'buy', 'sell', 'hold'
    confidence_score = Column(Float)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///arbitrage.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_arbitrage_db():
    Base.metadata.create_all(bind=engine) 