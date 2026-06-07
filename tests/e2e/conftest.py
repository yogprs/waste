import pytest
import subprocess
import time
import os
import sys
import urllib.request
import urllib.error

@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Memulai server Flask di background untuk pengujian E2E."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    env = os.environ.copy()
    
    process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=project_root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Tunggu sampai server Flask hidup (maksimal 30 detik)
    url = "http://localhost:3000/"
    server_ready = False
    for _ in range(30):
        try:
            res = urllib.request.urlopen(url)
            if res.getcode() == 200:
                server_ready = True
                break
        except urllib.error.URLError:
            time.sleep(1)
            
    if not server_ready:
        process.terminate()
        stdout, stderr = process.communicate()
        raise RuntimeError(f"Flask server gagal berjalan.\nSTDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}")
    
    yield
    
    # Mematikan server setelah pengujian selesai
    process.terminate()
    process.wait()
