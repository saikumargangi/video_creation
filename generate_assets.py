import os
try:
    from PIL import Image
    print("PIL imported successfully")
except ImportError:
    print("PIL not installed")
    exit(1)

def create_assets():
    os.makedirs("shared/assets/backgrounds", exist_ok=True)
    os.makedirs("shared/assets/character", exist_ok=True)

    print("Generating assets...")
    
    # Backgrounds
    Image.new('RGB', (1920, 1080), color=(200, 200, 200)).save('shared/assets/backgrounds/home.png')
    Image.new('RGB', (1920, 1080), color=(100, 100, 100)).save('shared/assets/backgrounds/street.png')
    Image.new('RGB', (1920, 1080), color=(220, 220, 250)).save('shared/assets/backgrounds/office.png')
    Image.new('RGB', (1920, 1080), color=(150, 150, 150)).save('shared/assets/backgrounds/warehouse.png')
    
    # Character
    Image.new('RGBA', (800, 1200), color=(255, 0, 0, 255)).save('shared/assets/character/main_character.png')
    
    print("Assets generated.")

if __name__ == "__main__":
    create_assets()
