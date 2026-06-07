import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:3000"

def set_auth_storage(page: Page):
    page.goto(BASE_URL)
    page.evaluate("""
        localStorage.setItem("user", JSON.stringify({
            "id": "e2e-test-user-id",
            "name": "E2E User",
            "email": "e2e@mail.com"
        }));
    """)

def test_profile_modal(page: Page):
    set_auth_storage(page)
    page.goto(f"{BASE_URL}/dashboard")
    
    # Buka menu profile dari header (desktop)
    page.locator("#nav-profile-trigger").evaluate("node => node.click()")
    
    # Klik tombol open profile pada dropdown
    page.locator("#open-profile").evaluate("node => node.click()")
    
    # Pastikan modal profile terbuka
    modal = page.locator("#profile-modal")
    expect(modal).to_be_visible()
    
    # Cek input form terisi dengan data user (dari set_auth_storage)
    expect(page.locator("#profile-name")).to_have_value("E2E User")
    expect(page.locator("#profile-email")).to_have_value("e2e@mail.com")
    
    # Tutup modal
    page.click("#close-modal")
    # Modal seharusnya sudah tidak tampil
    expect(modal).not_to_be_visible()
