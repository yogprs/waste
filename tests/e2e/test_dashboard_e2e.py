import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:3000"

def set_auth_storage(page: Page):
    """Bypass UI login dengan langsung set localStorage agar E2E lebih cepat"""
    page.goto(BASE_URL)
    page.evaluate("""
        localStorage.setItem("user", JSON.stringify({
            "id": "e2e-test-user-id",
            "name": "E2E User",
            "email": "e2e@mail.com"
        }));
    """)

def test_dashboard_page_elements(page: Page):
    set_auth_storage(page)
    
    # Kunjungi dashboard
    page.goto(f"{BASE_URL}/dashboard")
    
    # Pastikan pengguna berhasil masuk ke dashboard
    expect(page).to_have_url(f"{BASE_URL}/dashboard")
    
    # Cek elemen sapaan dan nama pengguna
    expect(page.locator("#greeting")).to_be_visible()
    expect(page.locator("#user-name")).to_have_text("E2E User")
    
    # Cek ketersediaan sidebar menu (Dasbor, Deteksi, Riwayat)
    sidebar_menus = page.locator("aside .sidebar-menu")
    expect(sidebar_menus).to_have_count(3)
    
    # Pastikan tombol "Mulai Pemindaian Baru" ada
    expect(page.locator("#identify-button")).to_be_visible()
