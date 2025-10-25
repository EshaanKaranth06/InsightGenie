# backend/api/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Scraper Config Schemas ---
class ScraperConfigBase(BaseModel):
    search_query: Optional[str] = None
    youtube_keywords: List[str] = []
    reddit_subreddits: List[str] = []
    # Add fields for other scrapers later if needed

class ScraperConfig(ScraperConfigBase):
    id: int
    product_id: int

    class Config:
        orm_mode = True # For SQLAlchemy compatibility (use from_attributes = True in Pydantic v2)

# --- Product Schemas ---
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    config: ScraperConfigBase # Nested config data

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[ScraperConfigBase] = None

class Product(BaseModel):
    id: int
    name: str
    owner_id: str
    config: Optional[ScraperConfig] = None

    class Config:
        orm_mode = True # For SQLAlchemy compatibility (use from_attributes = True in Pydantic v2)