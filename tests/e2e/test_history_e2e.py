import pytest
import re
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:3000"

def set_auth_storage(page: Page):
    page.goto(BASE_URL)
    page.evaluate("""
        localStorage.setItem("user", JSON.stringify({
            "id": "e2e-test-user-id",
            "name": "E2E User",
            "email": "e2e@mail.com",
            "role": "petugas"
        }));
    """)

def test_history_page(page: Page):
    set_auth_storage(page)
    page.goto(f"{BASE_URL}/history")
    
    # Cek label halaman
    expect(page.locator(".page-content-label")).to_have_text("Riwayat Deteksi")
    
    # Cek filter yang tersedia
    expect(page.locator(".filter-all")).to_be_visible()
    expect(page.locator(".filter-organic")).to_be_visible()
    expect(page.locator(".filter-non-organic")).to_be_visible()
    
    # Klik filter organik
    page.click(".filter-organic")
    
    # Pastikan filter berubah menjadi aktif
    expect(page.locator(".filter-organic")).to_have_class(re.compile(r"\bactive\b"))
