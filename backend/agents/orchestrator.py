import json
from google import genai
from google.genai import types
from schemas.agent_schemas import StrategyJSON, CriticResultJSON, DraftCandidate

# Initialize Gemini client (requires GEMINI_API_KEY env var)
client = genai.Client()

def plan_strategy(context_builder_output: str) -> StrategyJSON:
    """Agent 1: Plans the strategy based on context. Uses PRO (flagship) for complex reasoning."""
    prompt = f"Context:\n{context_builder_output}\n\nPlan the next conversational move."
    
    response = client.models.generate_content(
        model="gemini-3.1-pro-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction="You are the Strategy Planner. Output ONLY a flat JSON object with the exact keys and types: 'objective' (string), 'current_state' (string), 'desired_next_state' (string), 'approach' (string), 'tone' (string), 'directness' (float between 0.0 and 1.0), 'intensity' (float between 0.0 and 1.0), 'avoid' (array of strings). Do NOT wrap it in any parent object."
        )
    )
    return StrategyJSON.model_validate_json(response.text)

def generate_draft(strategy: StrategyJSON, context_builder_output: str, previous_draft: str = "", feedback: str = "") -> str:
    """Agent 2: Generates the actual prose message. Uses FLASH (efficient tier)."""
    sys_msg = "You are the Response Generator. Write a natural message executing the given strategy."
    if feedback:
        sys_msg += f"\nPrevious Draft: {previous_draft}\nCritic Feedback: {feedback}\nRevise the draft based on this feedback."
    
    prompt = f"Context:\n{context_builder_output}\n\nStrategy:\n{strategy.model_dump_json()}"
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=sys_msg
        )
    )
    return response.text

def critique_draft(draft: str, strategy: StrategyJSON) -> CriticResultJSON:
    """Agent 3: Critiques the draft against the strategy. Uses FLASH (efficient tier)."""
    prompt = f"Strategy:\n{strategy.model_dump_json()}\n\nDraft Message:\n{draft}\n\nCritique this draft."
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction="You are the Critic. Output ONLY a flat JSON object with the exact keys: 'passed' (boolean), 'scores' (dictionary of strings to ints), 'issues' (list of strings), 'revision_instructions' (list of strings). Do NOT wrap it in any parent object."
        )
    )
    
    try:
        return CriticResultJSON.model_validate_json(response.text)
    except Exception as e:
        # Fallback if LLM fails to output valid JSON
        return CriticResultJSON(
            passed=False, 
            scores={"error": 0}, 
            issues=["LLM output unparseable JSON"], 
            revision_instructions=["Ensure output is raw JSON matching the schema."]
        )

def run_agentic_loop(context_builder_output: str) -> DraftCandidate:
    """The Bounded Agentic Loop (Max 2 Revisions)."""
    # 1. Plan Strategy
    strategy = plan_strategy(context_builder_output)
    
    draft_content = ""
    critic_feedback = None
    
    # Bounded Loop
    for iteration in range(1, 4):  # max 3 tries (initial + 2 revisions)
        # 2. Generate
        feedback_str = json.dumps(critic_feedback.model_dump()) if critic_feedback else ""
        draft_content = generate_draft(strategy, context_builder_output, draft_content, feedback_str)
        
        # 3. Critique
        critic_result = critique_draft(draft_content, strategy)
        
        if critic_result.passed:
            return DraftCandidate(content=draft_content, strategy=strategy, critic_feedback=critic_result, iteration=iteration)
        
        critic_feedback = critic_result
    
    # If it fails all revisions, return the best available
    return DraftCandidate(content=draft_content, strategy=strategy, critic_feedback=critic_feedback, iteration=3)
