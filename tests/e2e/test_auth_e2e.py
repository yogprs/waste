import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:3000"

def test_login_flow(page: Page):
    test_email = "admin@waste.com"
    test_name = "Admin Sistem"
    test_password = "password123"

    page.on("dialog", lambda dialog: dialog.accept())

    # Mock login gagal
    page.route("**/api/login", lambda route: route.fulfill(
        status=401,
        content_type="application/json",
        json={"error": "Password salah"}
    ))

    page.goto(f"{BASE_URL}/login")

    page.fill("input#email", test_email)
    page.fill("input#password", "wrongpass")
    page.click("button.button-login")

    # Verifikasi error message muncul
    expect(page.locator("#errorMsg")).to_have_text("Password salah")

    # Mock login sukses
    page.unroute("**/api/login")
    page.route("**/api/login", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        json={
            "message": "Login berhasil",
            "user": {
                "id": "93fdf758-38da-401c-8440-a8b8af2431c3",
                "name": test_name,
                "email": test_email,
                "role": "admin"
            }
        }
    ))

    page.fill("input#password", test_password)
    page.click("button.button-login")

    # Harusnya diarahkan ke halaman dashboard jika sukses
    page.wait_for_url(f"{BASE_URL}/dashboard")
    expect(page).to_have_url(f"{BASE_URL}/dashboard")

    # Verifikasi nama pengguna muncul di dashboard
    expect(page.locator("#user-name")).to_have_text(test_name)
