import pytest
from models import OptionInput, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from sqlalchemy import func

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

def test_option_input_analytics(test_db):
    session = test_db()
    # Insert sample data
    for k in [100, 100, 110, 120]:
        row = OptionInput(S=100, K=k, T=1, r=0.05, sigma=0.2, option_type="call", purchase_price=10, timestamp=datetime.datetime.utcnow())
        session.add(row)
    session.commit()
    # Most-used strikes
    strike_counts = session.query(OptionInput.K, func.count(OptionInput.K)).group_by(OptionInput.K).all()
    assert (100, 2) in strike_counts
    # Most-used vol ranges
    for v in [0.2, 0.2, 0.3, 0.4]:
        row = OptionInput(S=100, K=100, T=1, r=0.05, sigma=v, option_type="call", purchase_price=10, timestamp=datetime.datetime.utcnow())
        session.add(row)
    session.commit()
    vol_counts = session.query(OptionInput.sigma).all()
    vols = [v[0] for v in vol_counts]
    assert vols.count(0.2) == 6 