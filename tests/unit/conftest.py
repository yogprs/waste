import sys
import os
import warnings
warnings.filterwarnings("ignore")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import pytest
from app import app, socketio, uploaded_users

# =========================
# Flask Test Client
# =========================
@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


# =========================
# Socket.IO Test Client
# =========================
@pytest.fixture
def socket_client():
    client = socketio.test_client(app)
    yield client
    client.disconnect()


# =========================
# Reset global state
# =========================
@pytest.fixture(autouse=True)
def clear_uploaded_users():
    uploaded_users.clear()