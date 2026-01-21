import os
import json
import logging
import time
import google.generativeai as genai
from typing import Type, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, ValidationError
from shared.schemas.schemas import (
    SeriesBible, SceneManifest, SceneLayout, SceneLayoutValidation, EditorPlan, JobRequest
)

logger = logging.getLogger(__name__)

# Configure Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not set. Agents will fail.")

T = TypeVar("T", bound=BaseModel)

class AgentError(Exception):
    pass

model = genai.GenerativeModel('gemini-1.5-flash')

def call_gemini_json(prompt: str, schema_cls: Type[T], retry_count: int = 2) -> T:
    """Calls Gemini and parses JSON output into a Pydantic model with retries."""
    
    schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)
    full_prompt = f"{prompt}\n\nOutput strictly valid JSON obeying this schema:\n{schema_json}"
    
    for attempt in range(retry_count + 1):
        try:
            response = model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
            text = response.text
            
            # Clean up potential markdown code blocks
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            data = json.loads(text)
            return schema_cls.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Attempt {attempt + 1}/{retry_count + 1} failed: {e}")
            if attempt == retry_count:
                raise AgentError(f"Failed to generate valid JSON for {schema_cls.__name__}: {e}")
        except Exception as e:
             logger.error(f"Gemini API error: {e}")
             if attempt == retry_count:
                raise AgentError(f"Gemini API failed: {e}")
             time.sleep(1)

    raise AgentError("Unknown error in call_gemini_json")


# --- Prompts ---

HEAD_WRITER_PROMPT = """You are a senior head writer from a world-class cartoon studio. Convert the story into a 5-minute screenplay with strong pacing and visual storytelling. Max 2 speaking characters. Dialogue is short and visual. Output ONLY screenplay text with scene headers."""

SERIES_BIBLE_PROMPT = """You are the Series Bible Director for a global cartoon channel. Create a strict continuity bible: one main character, fixed outfit, consistent colors, allowed locations, props, motion library, camera styles, style rules. Output ONLY valid JSON.

bible.json schema:
{
  "character": {"name": "string", "outfit": "string", "appearance_rules": ["string"]},
  "style": {"type": "2d_cartoon_clean", "rules": ["string"]},
  "locations": ["home","street","office","warehouse"],
  "props": ["phone","box","desk","chair"],
  "motion_library": ["idle","idle_talk","walk_in","walk_out","point","sit","stand","happy_jump","sad_idle","angry_talk"],
  "camera_styles": ["wide","medium","close","tracking"]
}"""

EPISODE_DIRECTOR_PROMPT = """You are an expert episode director. Split the screenplay into 18–24 scenes totaling 300 seconds (+/-2). Each scene 8–18 seconds. Use only bible locations and actions. Output ONLY valid JSON."""

SCENE_LAYOUT_PROMPT = """You are a senior layout artist. Generate one render-ready scene JSON. Use only bible locations/actions/cameras. Dialogue must be 1–2 short lines. Output ONLY valid JSON."""

CONTINUITY_SUPERVISOR_PROMPT = """You are a continuity supervisor. Validate ALL scene JSONs against the bible. Fix illegal values and shorten long dialogue. Ensure total duration ~300s. Output ONLY JSON: {issues_found:[], fixed_scenes:[]}."""

POST_PRODUCER_PROMPT = """You are a post-production producer. Create an assembly plan for stitching scenes. Output JSON with resolution=1920x1080 fps=30 format=mp4 subtitles=srt transitions disabled music disabled."""


# --- Agents ---

def head_writer_agent(story: str) -> str:
    # This one returns text, not JSON
    full_prompt = f"{HEAD_WRITER_PROMPT}\n\nSTORY:\n{story}"
    response = model.generate_content(full_prompt)
    return response.text

def series_bible_agent(script: str) -> SeriesBible:
    prompt = f"{SERIES_BIBLE_PROMPT}\n\nSCRIPT:\n{script[:2000]}..." # Truncate for context window if needed, though 1.5 flash has large window
    return call_gemini_json(prompt, SeriesBible)

def episode_director_agent(script: str, bible: SeriesBible) -> SceneManifest:
    bible_ctx = bible.model_dump_json()
    prompt = f"{EPISODE_DIRECTOR_PROMPT}\n\nBIBLE:\n{bible_ctx}\n\nSCRIPT:\n{script}"
    return call_gemini_json(prompt, SceneManifest)

def scene_layout_agent(scene_manifest_item: dict, bible: SeriesBible, script_context: str) -> SceneLayout:
    bible_ctx = bible.model_dump_json()
    scene_ctx = json.dumps(scene_manifest_item)
    # We provide a bit of script context around the scene if possible, or just the whole script
    prompt = f"{SCENE_LAYOUT_PROMPT}\n\nBIBLE:\n{bible_ctx}\n\nSCENE MANIFEST ITEM:\n{scene_ctx}\n\nCONTEXT:\n{script_context}"
    return call_gemini_json(prompt, SceneLayout)

def continuity_supervisor_agent(scenes: List[SceneLayout], bible: SeriesBible) -> SceneLayoutValidation:
    bible_ctx = bible.model_dump_json()
    scenes_ctx = json.dumps([s.model_dump() for s in scenes])
    prompt = f"{CONTINUITY_SUPERVISOR_PROMPT}\n\nBIBLE:\n{bible_ctx}\n\nSCENES:\n{scenes_ctx}"
    # This might return a huge JSON, be careful with token limits. 
    # For MVP we assume 18-24 scenes fit in context.
    return call_gemini_json(prompt, SceneLayoutValidation)

def post_producer_agent(scenes: List[SceneLayout]) -> EditorPlan:
    prompt = f"{POST_PRODUCER_PROMPT}\n\nNumber of scenes: {len(scenes)}"
    return call_gemini_json(prompt, EditorPlan)
