
from shared.schemas.schemas import JobRequest, JobStatus, SceneLayout

def test_job_request_schema():
    req = JobRequest(story="Test story", duration_seconds=60, style_pack="default")
    assert req.story == "Test story"
    assert req.duration_seconds == 60
    assert req.style_pack == "default"

def test_job_status_schema():
    status = JobStatus(
        job_id="123", status="processing", progress_current=10, progress_total=100
    )
    assert status.job_id == "123"
    assert status.status == "processing"

def test_scene_layout_schema():
    scene = SceneLayout(
        scene_id="1", 
        location="home", 
        action="sitting", 
        dialogue="hello", 
        camera="wide",
        duration=5.0,
        emotion="neutral",
        music_mood="cheerful"
    )
    assert scene.duration == 5.0
