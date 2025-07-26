import pytest
from historical_iv_models import OptionIVHistory, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

def test_option_iv_history_insert(test_db):
    session = test_db()
    row = OptionIVHistory(
        ticker="AAPL",
        expiry="2024-12-20",
        strike=100,
        option_type="call",
        iv=0.2,
        timestamp=datetime.datetime.utcnow()
    )
    session.add(row)
    session.commit()
    result = session.query(OptionIVHistory).filter_by(ticker="AAPL").first()
    assert result is not None
    assert result.strike == 100
    assert result.iv == 0.2 