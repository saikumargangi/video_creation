import os
try:
    from PIL import Image
    print("PIL imported successfully")
except ImportError:
    print("PIL not installed")
    exit(1)

def create_assets():
    # Use absolute path based on this script's location
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "shared", "assets")
    
    os.makedirs(os.path.join(ASSETS_DIR, "backgrounds"), exist_ok=True)
    os.makedirs(os.path.join(ASSETS_DIR, "character"), exist_ok=True)

    print(f"Generating assets in {ASSETS_DIR}...")
    
    # Backgrounds
    Image.new('RGB', (1920, 1080), color=(200, 200, 200)).save(os.path.join(ASSETS_DIR, 'backgrounds/home.png'))
    Image.new('RGB', (1920, 1080), color=(100, 100, 100)).save(os.path.join(ASSETS_DIR, 'backgrounds/street.png'))
    Image.new('RGB', (1920, 1080), color=(220, 220, 250)).save(os.path.join(ASSETS_DIR, 'backgrounds/office.png'))
    Image.new('RGB', (1920, 1080), color=(150, 150, 150)).save(os.path.join(ASSETS_DIR, 'backgrounds/warehouse.png'))
    
    # Character
    # Simple red rectangle character
    Image.new('RGBA', (800, 1200), color=(255, 0, 0, 255)).save(os.path.join(ASSETS_DIR, 'character/main_character.png'))
    
    print("Assets generated successfully.")

if __name__ == "__main__":
    create_assets()
