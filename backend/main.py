from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

from sqlalchemy import text
from db.database import engine, Base, get_db
from db import models
from agents.orchestrator import run_agentic_loop

# Base.metadata.create_all handles table creation automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Conversa API", version="0.1.0")

# Mount the frontend directory
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

class CreateCaseRequest(BaseModel):
    title: str
    target_name: str
    background_context: Optional[str] = None
    objective: str
    horizon: int = 5

class UpdateObjectiveRequest(BaseModel):
    objective: str

class AnalyzeRequest(BaseModel):
    case_id: str
    target_latest_message: str
    additional_context: Optional[str] = None

class AcceptDraftRequest(BaseModel):
    case_id: str
    target_message: str
    draft_content: str
    expected_state_version: int

@app.get("/")
def read_root():
    return FileResponse("../frontend/index.html")

@app.post("/cases")
def create_case(request: CreateCaseRequest, db: Session = Depends(get_db)):
    new_case = models.Case(
        title=request.title,
        target_name=request.target_name,
        background_context=request.background_context,
        objective=request.objective,
        horizon=request.horizon
    )
    db.add(new_case)
    
    initial_state = models.ConversationState(
        case_id=new_case.id,
        version=1,
        exchange_number=0,
        emotional_state="neutral"
    )
    db.add(initial_state)
    db.commit()
    
    return {"status": "success", "case_id": new_case.id}

@app.put("/cases/{case_id}/objective")
def update_objective(case_id: str, request: UpdateObjectiveRequest, db: Session = Depends(get_db)):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.objective = request.objective
    db.commit()
    return {"status": "success"}

@app.post("/analyze")
def analyze_and_draft(request: AnalyzeRequest, db: Session = Depends(get_db)):
    case = db.query(models.Case).filter(models.Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Fetch recent history
    recent_messages = db.query(models.Message).filter(
        models.Message.case_id == request.case_id
    ).order_by(models.Message.created_at.desc()).limit(10).all()
    
    history_text = "\n".join([f"{m.role}: {m.content}" for m in reversed(recent_messages)]) if recent_messages else "No previous messages."

    # REAL CONTEXT BUILDER
    context_output = f"""
    TARGET PROFILE / BACKSTORY:
    {case.background_context or 'None provided.'}

    CURRENT STRATEGIC OBJECTIVE:
    {case.objective}

    RECENT CONVERSATION HISTORY:
    {history_text}

    LATEST INCOMING MESSAGE (Target):
    {request.target_latest_message}
    
    ADDITIONAL USER NOTE / CONTEXT FOR THIS MESSAGE:
    {request.additional_context or 'None'}
    """
    
    # Run Orchestrator Loop
    try:
        final_draft = run_agentic_loop(context_output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent loop failed: {str(e)}")
    
    return {
        "status": "success",
        "draft": final_draft.model_dump()
    }

@app.post("/accept")
def accept_draft(request: AcceptDraftRequest, db: Session = Depends(get_db)):
    """Commits both the target's message and the accepted AI draft to the database."""
    current_state = db.query(models.ConversationState).filter(
        models.ConversationState.case_id == request.case_id
    ).order_by(models.ConversationState.version.desc()).first()
    
    if not current_state:
        raise HTTPException(status_code=404, detail="State not found")
        
    if current_state.version != request.expected_state_version:
        raise HTTPException(status_code=409, detail=f"Conflict: State version mismatch. Expected {request.expected_state_version} but got {current_state.version}.")
        
    # 1. Save Target's incoming message
    target_msg = models.Message(
        case_id=request.case_id,
        role="target",
        content=request.target_message
    )
    db.add(target_msg)
    
    # 2. Save System's outgoing message
    agent_msg = models.Message(
        case_id=request.case_id,
        role="system",
        content=request.draft_content
    )
    db.add(agent_msg)
    
    # 3. Advance the state
    new_state = models.ConversationState(
        case_id=request.case_id,
        version=current_state.version + 1,
        exchange_number=current_state.exchange_number + 1,
        emotional_state=current_state.emotional_state,
        unresolved_topics=current_state.unresolved_topics
    )
    db.add(new_state)
    
    db.commit()
    
    return {"status": "success", "new_state_version": new_state.version}

# To run: uvicorn backend.main:app --reload
