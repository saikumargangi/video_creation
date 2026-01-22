import os
import logging
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, ImageClip
from shared.schemas.schemas import SceneLayout

logger = logging.getLogger(__name__)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "shared", "assets")

def render_scene(scene: SceneLayout, output_path: str, character_path: str = None):
    """
    Renders a single scene to an MP4 file.
    """
    try:
        duration = scene.duration
        
        # 1. Background
        # Try to find a background image for the location, fallback to color
        bg_path = os.path.join(ASSETS_DIR, "backgrounds", f"{scene.location}.png")
        if os.path.exists(bg_path):
            bg_clip = ImageClip(bg_path).set_duration(duration)
            bg_clip = bg_clip.resize(newsize=(1280, 720))
        else:
            # Fallback color based on location name hash or simple logic
            color = (100, 100, 100)
            if "home" in scene.location: color = (200, 200, 220)
            elif "street" in scene.location: color = (100, 120, 100)
            elif "office" in scene.location: color = (220, 220, 250)
            
            bg_clip = ColorClip(size=(1280, 720), color=color, duration=duration)

        # 2. Main Character
        # Overlay character centered
        
        # Determine strict character path
        if not character_path or not os.path.exists(character_path):
             # Fallback to shared asset
             character_path = os.path.join(ASSETS_DIR, "character", "main_character.png")

        if os.path.exists(character_path):
             char_clip = ImageClip(character_path).set_duration(duration)
             # Simple "animation": maybe slight zoom or bounce?
             # For MVP: just static overlay
             # Resize to reasonable height relative to 720p
             char_clip = char_clip.resize(height=500).set_pos(("center", "bottom"))
             final_clip = CompositeVideoClip([bg_clip, char_clip])
        else:
             # Fallback if no character asset
             logger.warning(f"Character asset not found at {character_path}")
             final_clip = bg_clip

        # 3. Subtitles / Dialogue
        if scene.dialogue:
            # Ensure imagemagick is installed for TextClip
            # On failures, we might skip text or use a basic font
            try:
                txt_clip = TextClip(scene.dialogue, fontsize=40, color='white', font='Liberation-Sans-Bold', stroke_color='black', stroke_width=2, size=(1100, None), method='caption')
                txt_clip = txt_clip.set_position(('center', 0.85), relative=True).set_duration(duration)
                final_clip = CompositeVideoClip([final_clip, txt_clip])
            except Exception as e:
                logger.error(f"Failed to generate TextClip: {e}")

        final_clip.fps = 30
        final_clip.write_videofile(
            output_path, 
            fps=24, # Lower FPS to save CPU
            codec="libx264", 
            audio=False, 
            verbose=False, 
            logger=None,
            preset="ultrafast", # Faster encoding, less memory
            threads=1 # Single thread to reduce memory peak
        )
        
    except Exception as e:
        logger.error(f"Error rendering scene {scene.scene_id}: {e}")
        # Create a red error clip so pipeline doesn't break completely
        error_clip = ColorClip(size=(1280, 720), color=(255, 0, 0), duration=scene.duration)
        error_clip.fps = 24
        error_clip.write_videofile(output_path, fps=24, codec="libx264", preset="ultrafast")
