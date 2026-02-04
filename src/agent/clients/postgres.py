import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.agent.domain.models import Base

# Get DB URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://coffee_admin:coffee_password@localhost:5440/coffee_shop")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
