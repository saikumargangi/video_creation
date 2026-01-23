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


# Debug: List available models to stderr
try:
    print("Available Gemini Models:", flush=True)
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}", flush=True)
except Exception as e:
    logger.warning(f"Failed to list models: {e}")

model = genai.GenerativeModel('gemini-2.0-flash')

def call_gemini_json(prompt: str, schema_cls: Type[T], retry_count: int = 2) -> T:
    """Calls Gemini and parses JSON output into a Pydantic model with retries."""
    
    schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)
    full_prompt = f"{prompt}\n\nOutput strictly valid JSON obeying this schema:\n{schema_json}"
    
    for attempt in range(retry_count + 1):
        try:
            # Basic rate limiting to prevent 429 Resource Exhausted
            time.sleep(2)
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
            
            # Robustness: Handle list wrapping if we expect a single item
            # If data is a list of 1 item, and schema_cls is likely a Model (not a List type hint), unwrap it.
            if isinstance(data, list) and len(data) == 1:
                 # Be optimistic and try to unwrap if validation fails on the list itself, or just try to validate the item
                 try:
                     return schema_cls.model_validate(data[0])
                 except ValidationError:
                     # If unwrapping fails validation, maybe it WAS supposed to be a list, fall through to normal validation
                     pass
            
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

HEAD_WRITER_PROMPT = """You are a senior head writer from a world-class cartoon studio. Convert the story into a short 15-second teaser screenplay. Max 2 speaking characters. Dialogue is extremely short and visual. Output ONLY screenplay text with scene headers."""

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

EPISODE_DIRECTOR_PROMPT = """You are an expert episode director. Split the screenplay into exactly 3 scenes totaling 15 seconds (+/-2). Each scene 4–6 seconds. Use only bible locations and actions. Output ONLY valid JSON."""

SCENE_LAYOUT_PROMPT = """You are a senior layout artist. Generate one render-ready scene JSON. Output a SINGLE JSON object (not a list). Use only bible locations/actions/cameras. Dialogue must be 1–2 short lines."""

CONTINUITY_SUPERVISOR_PROMPT = """You are a continuity supervisor. Validate ALL scene JSONs against the bible. Fix illegal values and shorten long dialogue. Ensure total duration ~15s. Output ONLY JSON: {issues_found:[], fixed_scenes:[]}."""

POST_PRODUCER_PROMPT = """You are a post-production producer. Create an assembly plan for stitching scenes. Output JSON with resolution=1920x1080 fps=30 format=mp4 subtitles=srt transitions disabled music disabled."""

CHARACTER_DESIGNER_PROMPT = """You are a prompt engineer for an image generation model.
Convert this character description into a precise, comma-separated image generation prompt.
Description: {description}
Output ONLY the prompt text."""


# --- Agents ---

def head_writer_agent(story: str) -> str:
    # This one returns text, not JSON
    full_prompt = f"{HEAD_WRITER_PROMPT}\n\nSTORY:\n{story}"
    response = model.generate_content(full_prompt)
    return response.text

def series_bible_agent(script: str) -> SeriesBible:
    prompt = f"{SERIES_BIBLE_PROMPT}\n\nSCRIPT:\n{script[:2000]}..." # Truncate for context window if needed, though 1.5 flash has large window
    return call_gemini_json(prompt, SeriesBible)

def character_designer_agent(bible: SeriesBible, output_path: str) -> bool:
    """Generates a character image and saves it to output_path."""
    try:
        # 1. Generate the Image Prompt
        description = f"Name: {bible.character.name}. Outfit: {bible.character.outfit}. Appearance: {', '.join(bible.character.appearance_rules)}."
        prompt_maker_prompt = CHARACTER_DESIGNER_PROMPT.format(description=description)
        response = model.generate_content(prompt_maker_prompt) # Uses standard text model
        image_prompt = response.text.strip()
        
        logger.info(f"Generated Image Prompt: {image_prompt}")

        # 2. Generate the Image using proper SDK method
        # 'gemini-2.0-flash' and specific image models can generate images via generate_content
        # We try the specific one first, then the general one
        candidate_models = [
            "gemini-2.0-flash-exp", # Often supports multimodal output
            "gemini-2.0-flash",
        ]
        
        # Check logs for available models, use one if found
        # Hardcoding the one we saw in logs:
        image_model_name = "gemini-2.0-flash-exp" # Trying standard 2.0 first as it is multimodal
        
        # Actually, let's look at the logs provided by user:
        # - models/gemini-2.0-flash-exp-image-generation
        # This is the gold standard if available.
        target_model = "gemini-2.0-flash-exp-image-generation"
        
        try:
            logging.info(f"Attempting image generation with {target_model}")
            img_gen_model = genai.GenerativeModel(target_model)
            # Force image generation intent
            response = img_gen_model.generate_content(f"Generate an image of {image_prompt}")
            
            # Check for image parts
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        # Decode and save
                        import base64
                        image_bytes = part.inline_data.data
                        from PIL import Image
                        import io
                        image = Image.open(io.BytesIO(image_bytes))
                        image.save(output_path)
                        logger.info(f"Character image saved to {output_path}")
                        return True
            
            logger.warning(f"No image parts found in response from {target_model}. Response: {response}")

            # Fallback to standard 2.0-flash-exp (multimodal) if specialized model returns text
            logger.info("Falling back to gemini-2.0-flash-exp-image-generation...")
            # Try specific image model again or a different preview if available
            fallback_model_name = "gemini-2.0-flash-exp" # Multimodal fallback
            fallback_model = genai.GenerativeModel(fallback_model_name)
            response = fallback_model.generate_content(f"Generate an image of {image_prompt}")
            if response.parts:
                for part in response.parts:
                     if part.inline_data:
                        import base64
                        from PIL import Image
                        import io
                        image = Image.open(io.BytesIO(part.inline_data.data))
                        image.save(output_path)
                        logger.info(f"Character image saved with fallback model to {output_path}")
                        return True
            
        except Exception as e:
            logger.error(f"Failed generation: {e}")
            
        return False

    except Exception as e:
        logger.error(f"Character Designer Agent failed: {e}")
        return False

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
