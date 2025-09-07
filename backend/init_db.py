
from sqlalchemy import create_engine
from db.models import Base
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./feedback.db")
engine = create_engine(DB_URL)

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")
