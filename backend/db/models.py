import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Case(Base):
    __tablename__ = "cases"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True)
    target_name = Column(String)
    background_context = Column(Text, nullable=True)
    objective = Column(Text)
    horizon = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConversationState(Base):
    __tablename__ = "conversation_states"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"))
    version = Column(Integer, default=1)
    exchange_number = Column(Integer, default=0)
    emotional_state = Column(String)
    unresolved_topics = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

class StateEvent(Base):
    __tablename__ = "state_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"))
    state_version = Column(Integer)
    event_type = Column(String)  # e.g., MESSAGE_RECEIVED, DRAFT_ACCEPTED
    payload = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"))
    role = Column(String)  # 'user', 'target', 'system'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Memory(Base):
    __tablename__ = "memories"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"))
    type = Column(String)  # 'episodic', 'semantic'
    content = Column(Text)
    source_message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    confidence = Column(Float, default=1.0)
    status = Column(String, default="active")  # 'active', 'deprecated', 'candidate'
    embedding = Column(JSON)  # Switched to JSON temporarily for SQLite compatibility
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
