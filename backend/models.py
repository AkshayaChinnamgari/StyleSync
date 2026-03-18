from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    avatar = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    body_type = Column(String, nullable=True)  # e.g., "Apple", "Pear", "Hourglass"
    style_type = Column(String, nullable=True)  # e.g., "Casual Chic", "Minimalist"
    
    garments = relationship("Garment", back_populates="owner", cascade="all, delete-orphan")
    outfit_history = relationship("OutfitHistory", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Garment(Base):
    __tablename__ = "garments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    filename = Column(String, index=True)
    color = Column(String)
    category = Column(String, index=True)
    style = Column(String)  # e.g., "casual", "formal", "sport"
    season = Column(String)  # e.g., "spring", "summer", "fall", "winter"
    fabric = Column(String, nullable=True)  # e.g., "cotton", "denim", "wool"
    size = Column(String)  # e.g., "S", "M", "L", "XL"
    brand = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    owner = relationship("User", back_populates="garments")
    outfit_items = relationship("OutfitItem", back_populates="garment")


class OutfitHistory(Base):
    __tablename__ = "outfit_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    occasion = Column(String)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    notes = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="outfit_history")
    outfit_items = relationship("OutfitItem", back_populates="outfit_history")


class OutfitItem(Base):
    __tablename__ = "outfit_items"
    id = Column(Integer, primary_key=True, index=True)
    outfit_id = Column(Integer, ForeignKey("outfit_history.id"), index=True)
    garment_id = Column(Integer, ForeignKey("garments.id"), index=True)
    
    outfit_history = relationship("OutfitHistory", back_populates="outfit_items")
    garment = relationship("Garment", back_populates="outfit_items")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    preferred_colors = Column(JSON, default=list)  # List of preferred hex colors
    preferred_styles = Column(JSON, default=list)  # List of style preferences
    preferred_brands = Column(JSON, default=list)  # List of brand preferences
    skin_tone = Column(String, nullable=True)
    budget_range = Column(String, nullable=True)
    
    user = relationship("User", back_populates="preferences")
