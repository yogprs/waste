import pytest
from playwright.sync_api import Page, expect
import uuid

BASE_URL = "http://127.0.0.1:3000"

def test_register_and_login_flow(page: Page):
    # Buat email unik untuk test
    uid = str(uuid.uuid4())[:8]
    test_email = f"testuser_{uid}@mail.com"
    test_name = f"Test User {uid}"
    test_password = "password123"

    # Mock API responses to guarantee E2E stability
    page.route("**/api/register", lambda route: route.fulfill(status=201, json={"message": "Register success"}))
    page.route("**/api/login", lambda route: route.fulfill(status=200, json={"user": {"id": "123", "name": test_name, "email": test_email}}))

    # 1. Pendaftaran
    page.goto(f"{BASE_URL}/register")
    
    # Isi form
    page.fill("input#name", test_name)
    page.fill("input#email", test_email)
    page.fill("input#password", test_password)
    page.fill("input#confirm", test_password)
    
    # Submit
    page.click("button[type='submit']")
    
    # Harusnya diarahkan ke halaman login jika sukses
    page.wait_for_url(f"{BASE_URL}/login")
    expect(page).to_have_url(f"{BASE_URL}/login")

    # 2. Login
    # Isi form login
    page.fill("input#email", test_email)
    page.fill("input#password", test_password)
    
    # Submit login
    page.click("button[type='submit']")
    
    # Harusnya diarahkan ke halaman dashboard jika sukses
    page.wait_for_url(f"{BASE_URL}/dashboard")
    expect(page).to_have_url(f"{BASE_URL}/dashboard")
    
    # Verifikasi data pengguna yang terlogin
    expect(page.locator("#user-name")).to_have_text(test_name)
    expect(page.locator("#email")).to_have_text(test_email)
