import pytest
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

def test_detection_page(page: Page):
    set_auth_storage(page)
    page.goto(f"{BASE_URL}/detection")
    
    # Cek tampilan utama deteksi
    expect(page.locator(".page-content-label")).to_have_text("Analisis Cerdas")
    expect(page.locator("h1.page-content-headline")).to_contain_text("Kenali Sampah Anda")
    
    # Cek area drop image ada
    expect(page.locator("#drop-area")).to_be_visible()
    
    # Cek ketersediaan tombol kamera
    expect(page.locator("#camera-button")).to_be_visible()
