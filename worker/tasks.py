import os
import json
import logging
from celery import chain, chord
from celery_app import celery_app
from agents import (
    head_writer_agent, series_bible_agent, episode_director_agent, 
    scene_layout_agent, continuity_supervisor_agent, post_producer_agent
)
from renderer import render_scene
from shared.schemas.schemas import SceneLayout
import subprocess

logger = logging.getLogger(__name__)

JOBS_DIR = os.getenv("JOBS_DIR", "/jobs")

def update_job_status(job_id, status, progress=0, message=None):
    job_dir = os.path.join(JOBS_DIR, job_id)
    status_file = os.path.join(job_dir, "status.json")
    
    data = {
        "job_id": job_id,
        "status": status,
        "progress_current": progress,
        "progress_total": 100, # Approximate
        "message": message or status
    }
    
    with open(status_file, "w") as f:
        json.dump(data, f)

@celery_app.task(name="tasks.generate_character_only")
def generate_character_only(job_id, prompt):
    update_job_status(job_id, "generating", 0, "Designing character...")
    
    job_dir = os.path.join(JOBS_DIR, job_id)
    job_assets_dir = os.path.join(job_dir, "assets")
    os.makedirs(job_assets_dir, exist_ok=True)
    character_path = os.path.join(job_assets_dir, "character.png")
    
    from agents import generate_character_image
    if generate_character_image(prompt, character_path):
        update_job_status(job_id, "completed", 100, "Character ready")
    else:
        update_job_status(job_id, "failed", 0, "Character generation failed")
        
    return {"job_id": job_id, "status": "completed"}

@celery_app.task(name="tasks.process_story")
def process_story(job_id, request_data):
    update_job_status(job_id, "planning", 10, "Head Writer creating script...")
    
    job_dir = os.path.join(JOBS_DIR, job_id)
    
    try:
        story = request_data.get("story")
        
        # 1. Head Writer
        script = head_writer_agent(story)
        with open(os.path.join(job_dir, "script.txt"), "w") as f:
            f.write(script)
            
        update_job_status(job_id, "planning", 20, "Creating Series Bible...")
        
        # 2. Series Bible
        bible = series_bible_agent(script)
        with open(os.path.join(job_dir, "bible.json"), "w") as f:
            f.write(bible.model_dump_json(indent=2))
            
        update_job_status(job_id, "planning", 25, "Checking character assets...")
        
        # 2.5 Character Designer
        # Ensure job assets dir exists
        job_assets_dir = os.path.join(job_dir, "assets")
        os.makedirs(job_assets_dir, exist_ok=True)
        character_path = os.path.join(job_assets_dir, "character.png")
        
        # KEY CHANGE: Check if character already exists (from linked job)
        if os.path.exists(character_path):
             logger.info("Using existing character asset from linked job.")
             update_job_status(job_id, "planning", 30, "Using approved character")
        else:
            # Generate from scratch if no pre-approved character
            from agents import character_designer_agent
            if character_designer_agent(bible, character_path):
                 update_job_status(job_id, "planning", 30, "Character created successfully")
            else:
                 logger.warning("Character generation failed, using fallback.")
                 update_job_status(job_id, "planning", 30, "Character generation failed, using fallback")
            
        update_job_status(job_id, "planning", 35, "Director planning scenes...")
        
        # 3. Episode Director
        manifest = episode_director_agent(script, bible)
        with open(os.path.join(job_dir, "scene_manifest.json"), "w") as f:
            f.write(manifest.model_dump_json(indent=2))
            
        # 4. Scene Layout (Parallel) - Prepare tasks
        scene_tasks = []
        for scene_item in manifest.scenes:
            # We pass dicts to celery tasks to avoid serialization issues with custom objects if any
            scene_tasks.append(generate_scene_layout.s(job_id, scene_item.model_dump(), bible.model_dump(), script))
            
        # Execute parallel layout generation, then continuity check
        workflow = chord(scene_tasks)(continuity_check_and_render.s(job_id, bible.model_dump()))
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_job_status(job_id, "failed", 0, str(e))
        raise e

@celery_app.task(name="tasks.generate_scene_layout")
def generate_scene_layout(job_id, scene_item_dict, bible_dict, script):
    from shared.schemas.schemas import SeriesBible # Re-import inside task
    bible = SeriesBible(**bible_dict)
    
    layout = scene_layout_agent(scene_item_dict, bible, script)
    
    # Save individual scene layout for debugging
    job_dir = os.path.join(JOBS_DIR, job_id)
    scene_path = os.path.join(job_dir, "scenes", f"{layout.scene_id:03d}.json")
    with open(scene_path, "w") as f:
        f.write(layout.model_dump_json(indent=2))
        
    return layout.model_dump()

@celery_app.task(name="tasks.continuity_check_and_render")
def continuity_check_and_render(scene_layouts_dicts, job_id, bible_dict):
    update_job_status(job_id, "planning", 50, "Continuity Supervisor checking...")
    
    from shared.schemas.schemas import SeriesBible, SceneLayout
    bible = SeriesBible(**bible_dict)
    scenes = [SceneLayout(**s) for s in scene_layouts_dicts]
    
    # 5. Continuity Supervisor
    validation = continuity_supervisor_agent(scenes, bible)
    final_scenes = validation.fixed_scenes
    
    job_dir = os.path.join(JOBS_DIR, job_id)
    with open(os.path.join(job_dir, "debug_report.json"), "w") as f:
        f.write(validation.model_dump_json(indent=2))

    # 6. Post Producer Plan
    editor_plan = post_producer_agent(final_scenes)
    
    # 7. Render Scenes (Parallel)
    render_tasks = []
    for scene in final_scenes:
        render_tasks.append(render_scene_task.s(job_id, scene.model_dump()))
        
    # Execute render, then assembly
    workflow = chord(render_tasks)(assemble_video.s(job_id))

@celery_app.task(name="tasks.render_scene_task")
def render_scene_task(job_id, scene_dict):
    from shared.schemas.schemas import SceneLayout
    scene = SceneLayout(**scene_dict)
    
    job_dir = os.path.join(JOBS_DIR, job_id)
    output_path = os.path.join(job_dir, "scenes", f"{scene.scene_id:03d}.mp4")
    
    # Check for job-specific character asset
    character_path = os.path.join(job_dir, "assets", "character.png")
    
    # Update status per scene? Might be too spammy. 
    # Just do the work.
    render_scene(scene, output_path, character_path=character_path)
    return output_path

@celery_app.task(name="tasks.assemble_video")
def assemble_video(scene_paths, job_id):
    update_job_status(job_id, "assembling", 90, "Stitching final video...")
    
    job_dir = os.path.join(JOBS_DIR, job_id)
    final_dir = os.path.join(job_dir, "final")
    list_path = os.path.join(final_dir, "list.txt")
    output_path = os.path.join(final_dir, "final.mp4")
    
    # Sort paths just in case
    scene_paths.sort()
    
    with open(list_path, "w") as f:
        for path in scene_paths:
            if path and os.path.exists(path):
                f.write(f"file '{path}'\n")
    
    # Run FFmpeg Concat
    # ffmpeg -f concat -safe 0 -i list.txt -c copy final.mp4
    cmd = [
        "ffmpeg", "-y", 
        "-f", "concat", 
        "-safe", "0", 
        "-i", list_path, 
        "-c", "copy", 
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    
    update_job_status(job_id, "completed", 100, "Ready to download")
    return output_path
