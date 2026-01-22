
import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock moviepy before importing renderer
sys.modules["moviepy.editor"] = MagicMock()
sys.modules["moviepy.editor"].ColorClip = MagicMock()
sys.modules["moviepy.editor"].TextClip = MagicMock()
sys.modules["moviepy.editor"].CompositeVideoClip = MagicMock()
sys.modules["moviepy.editor"].ImageClip = MagicMock()

from worker.renderer import render_scene
from shared.schemas.schemas import SceneLayout

class TestRenderer(unittest.TestCase):
    @patch("worker.renderer.os.path.exists")
    @patch("worker.renderer.CompositeVideoClip")
    @patch("worker.renderer.ColorClip")
    def test_render_scene_fallback(self, mock_color_clip, mock_composite, mock_exists):
        # Setup
        mock_exists.return_value = False # Force fallback
        
        scene = SceneLayout(
             scene_id="1", 
             location="home", 
             action="sitting", 
             dialogue="hello", 
             camera="wide",
             duration=5.0,
             emotion="happy",
             music_mood="calm"
        )
        
        # Execute
        render_scene(scene, "output.mp4")
        
        # Assertions
        # Should create a ColorClip because assets are missing
        mock_color_clip.assert_called() 
        
    @patch("worker.renderer.os.path.exists")
    @patch("worker.renderer.ImageClip")
    @patch("worker.renderer.CompositeVideoClip")
    def test_render_scene_with_assets(self, mock_composite, mock_image_clip, mock_exists):
        # Setup
        mock_exists.return_value = True # Assets exist
        
        scene = SceneLayout(
             scene_id="2", 
             location="home", 
             action="sitting", 
             dialogue="hello", 
             camera="wide",
             duration=5.0,
             emotion="happy",
             music_mood="calm"
        )
        
        # Execute
        render_scene(scene, "output.mp4")
        
        # Assertions
        # Should create ImageClip
        mock_image_clip.assert_called()
