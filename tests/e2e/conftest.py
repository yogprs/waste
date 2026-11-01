import pytest
import subprocess
import time
import os
import sys
import urllib.request
import urllib.error

SERVER_URL = "http://127.0.0.1:3000/"

def is_server_ready():
    try:
        res = urllib.request.urlopen(SERVER_URL, timeout=1)
        return res.getcode() == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False

@pytest.fixture(scope="session", autouse=True)
def start_server():
    """Memastikan server Flask berjalan untuk pengujian E2E."""
    # Jika server sudah berjalan (misal dijalankan manual di terminal lain), langsung pakai
    if is_server_ready():
        yield
        return

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    env = os.environ.copy()
    env["FLASK_DEBUG"] = "false"
    env["FLASK_USE_RELOADER"] = "false"
    env["TF_ENABLE_ONEDNN_OPTS"] = "0"
    env["TF_CPP_MIN_LOG_LEVEL"] = "2"
    
    # Jalankan app.py
    process = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=project_root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Tunggu sampai server Flask hidup (maksimal 60 detik)
    server_ready = False
    for _ in range(60):
        if is_server_ready():
            server_ready = True
            break
        time.sleep(1)
            
    if not server_ready:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        raise RuntimeError("Flask server gagal berjalan dalam batas waktu 60 detik.")
    
    yield
    
    # Mematikan server setelah pengujian selesai
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
