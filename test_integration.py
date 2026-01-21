import requests
import time
import sys
import os

API_URL = "http://localhost:8000"

def test_pipeline():
    print("🚀 Starting integration test...")
    
    # 1. Submit Job
    payload = {
        "story": "A robot finds a flower in a scrapyard. It is surprised and happy. It takes the flower home.",
        "duration_seconds": 60, # Shorten for test
        "style_pack": "basic_cartoon_v1"
    }
    
    try:
        response = requests.post(f"{API_URL}/generate", json=payload)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"✅ Job submitted: {job_id}")
    except Exception as e:
        print(f"❌ Failed to submit job: {e}")
        sys.exit(1)

    # 2. Poll Status
    print("⏳ Polling for completion...")
    start_time = time.time()
    while True:
        try:
            status_res = requests.get(f"{API_URL}/status/{job_id}")
            status_data = status_res.json()
            status = status_data["status"]
            progress = status_data.get("progress_current", 0)
            message = status_data.get("message", "")
            
            print(f"   Status: {status} ({progress}%) - {message}")
            
            if status == "completed":
                print("✅ Job completed!")
                break
            elif status == "failed":
                print(f"❌ Job failed: {message}")
                sys.exit(1)
                
            if time.time() - start_time > 600: # 10 min timeout
                print("❌ Timeout waiting for job completion")
                sys.exit(1)
                
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Error polling status: {e}")
            time.sleep(5)

    # 3. Verify Download
    print("📥 Verifying download...")
    try:
        download_res = requests.get(f"{API_URL}/download/{job_id}", stream=True)
        if download_res.status_code == 200:
            with open(f"final_{job_id}.mp4", "wb") as f:
                for chunk in download_res.iter_content(chunk_size=8192): 
                    f.write(chunk)
            print("✅ Video downloaded successfully.")
            
            # Simple size check
            size = os.path.getsize(f"final_{job_id}.mp4")
            print(f"   Video size: {size / 1024 / 1024:.2f} MB")
            if size > 1000:
                print("✅ Video seems valid (size > 1KB)")
            else:
                print("❌ Video file is too small")
                sys.exit(1)
                
        else:
            print(f"❌ Download failed: {download_res.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_pipeline()
