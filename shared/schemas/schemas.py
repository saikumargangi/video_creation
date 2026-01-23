from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# --- API Request/Response Schemas ---

class VoiceConfig(BaseModel):
    enabled: bool = False
    language: str = "en"
    gender: str = "male"

class JobRequest(BaseModel):
    story: str
    duration_seconds: int = 300
    style_pack: str = "basic_cartoon_v1"
    subtitles: bool = True
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    character_job_id: Optional[str] = None # Link to pre-generated character

class CharacterRequest(BaseModel):
    prompt: str = "A friendly robot"

class JobResponse(BaseModel):
    job_id: str
    status: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress_current: int
    progress_total: int
    message: Optional[str] = None
    artifacts: Optional[dict] = None

# --- Agent Output Schemas ---

class BibleCharacter(BaseModel):
    name: str
    outfit: str
    appearance_rules: List[str]

class BibleStyle(BaseModel):
    type: str = "2d_cartoon_clean"
    rules: List[str]

class SeriesBible(BaseModel):
    character: BibleCharacter
    style: BibleStyle
    locations: List[str]
    props: List[str]
    motion_library: List[str]
    camera_styles: List[str]

class SceneManifestItem(BaseModel):
    scene_id: int
    duration: int
    location: str
    beats: str

class SceneManifest(BaseModel):
    total_duration: int
    scenes: List[SceneManifestItem]

class SceneLayout(BaseModel):
    scene_id: int
    duration: int
    location: str
    camera: str
    action: str
    emotion: str
    dialogue: str
    sfx: List[str] = []
    music_mood: str

class SceneLayoutValidation(BaseModel):
    issues_found: List[str]
    fixed_scenes: List[SceneLayout]

class EditorPlan(BaseModel):
    resolution: str = "1920x1080"
    fps: int = 30
    format: str = "mp4"
    subtitles_format: str = "srt"
    transitions: bool = False
    music: bool = False
