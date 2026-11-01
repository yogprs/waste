document.addEventListener("DOMContentLoaded", () => {
  function truncateText(text, maxLength) {
    if (!text) return "";
    if (text.length > maxLength) {
      return text.substring(0, maxLength) + "...";
    }
    return text;
  }

  function logout() {
    const logoutElement = document.querySelector(".nav-menu-item.logout");
    if (!logoutElement) return;

    logoutElement.addEventListener("click", () => {
      localStorage.clear();
      sessionStorage.clear();

      window.location.href = "/";
    });
  }

  function navbarProfile() {
    const nameUser = document.getElementById("nav-user-name");
    const email = document.getElementById("nav-email");
    const image = document.getElementById("nav-image-user");

    const storage = localStorage.getItem("user");
    if (!storage) return;

    const data = JSON.parse(storage);
    if (!data) return;

    if (nameUser) nameUser.textContent = truncateText(data.name, 10);
    if (email) email.textContent = truncateText(data.email, 10);
    if (image) image.src = `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(data.name || "?")}`;
  }

  function navbarProfileHandler() {
    const trigger = document.getElementById("nav-profile-trigger");
    const menu = document.getElementById("nav-profile-menu");
    const openProfile = document.getElementById("open-profile");
    const dashboardProfile = document.getElementById("dashboard-profile");
    const sidebarUser = document.querySelector(".sidebar-user");
    const modal = document.getElementById("profile-modal");

    // Ambil data user dari localStorage
    const storage = localStorage.getItem("user");
    const user = storage ? JSON.parse(storage) : null;

    if (!trigger || !menu) return;

    let isOpen = false;

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();

      isOpen = !isOpen;
      menu.classList.toggle("active", isOpen);
    });

    document.addEventListener("click", (e) => {
      if (
        !menu.contains(e.target) &&
        !e.target.closest("#nav-profile-trigger")
      ) {
        menu.classList.remove("active");
        isOpen = false;
      }
    });

    menu.addEventListener("click", (e) => {
      e.stopPropagation();
    });

    // Klik "Profile" di dropdown -> buka modal profile
    if (openProfile) {
      openProfile.addEventListener("click", () => {
        if (!modal) return;
        modal.classList.add("active");

        const latestStorage = localStorage.getItem("user");
        const latestUser = latestStorage ? JSON.parse(latestStorage) : null;
        if (latestUser) {
          const nameInput = document.getElementById("profile-name");
          const emailInput = document.getElementById("profile-email");
          const passwordInput = document.getElementById("password");
          if (nameInput) nameInput.value = latestUser.name || "";
          if (emailInput) emailInput.value = latestUser.email || "";
          if (passwordInput) passwordInput.value = "";
        }

        const errEl = document.getElementById("errorMsg");
        if (errEl) errEl.innerText = "";

        menu.classList.remove("active");
        isOpen = false;
      });
    }

    if (dashboardProfile) {
      dashboardProfile.addEventListener("click", () => {
        window.location.href = "/dashboard";
      });
    }

    // Halaman TANPA sidebar: tangani profile form submit & delete di sini
    if (!sidebarUser) {
      const closeModal = document.getElementById("close-modal");
      const nameInput = document.getElementById("profile-name");
      const emailInput = document.getElementById("profile-email");
      const passwordInput = document.getElementById("password");

      if (!modal) return;

      // Tutup modal
      if (closeModal) {
        closeModal.addEventListener("click", (e) => {
          e.preventDefault();
          modal.classList.remove("active");
        });
      }

      // Klik luar modal -> tutup
      window.addEventListener("click", (e) => {
        if (e.target === modal) {
          modal.classList.remove("active");
        }
      });

      // Submit form — Update profile
      const profileForm = document.getElementById("profile-form");
      if (profileForm) {
        profileForm.addEventListener("submit", async (e) => {
          e.preventDefault();
          const errEl = document.getElementById("errorMsg");
          if (errEl) { errEl.style.color = "red"; errEl.innerText = ""; }

          const storedUser = localStorage.getItem("user");
          const currentUser = storedUser ? JSON.parse(storedUser) : null;
          if (!currentUser) {
            window.location.href = "/login";
            return;
          }

          const nameVal = nameInput ? nameInput.value.trim() : "";
          const emailVal = emailInput ? emailInput.value.trim() : "";
          const passwordVal = passwordInput ? passwordInput.value : "";

          if (!nameVal || !emailVal) {
            if (errEl) errEl.innerText = "Nama dan email wajib diisi.";
            return;
          }

          const submitBtn = document.querySelector("#profile-form .btn-save");
          if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Menyimpan..."; }

          try {
            const body = { updatedUser: { name: nameVal, email: emailVal } };
            if (passwordVal && passwordVal.length > 0) {
              body.updatedUser.password = passwordVal;
            }

            const res = await fetch(`/api/profile/${currentUser.role}/${currentUser.id}`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body),
            });

            const json = await res.json();

            if (res.ok) {
              // Simpan data terbaru ke localStorage
              const updatedUser = {
                ...currentUser,
                name: json.data?.name || nameVal,
                email: json.data?.email || emailVal,
              };
              localStorage.setItem("user", JSON.stringify(updatedUser));

              if (errEl) { errEl.style.color = "green"; errEl.innerText = "Profile berhasil diperbarui."; }

              // Refresh tampilan navbar
              const navName = document.getElementById("nav-user-name");
              const navEmail = document.getElementById("nav-email");
              const navImg = document.getElementById("nav-image-user");
              if (navName) navName.textContent = truncateText(updatedUser.name, 10);
              if (navEmail) navEmail.textContent = truncateText(updatedUser.email, 10);
              if (navImg) navImg.src = `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(updatedUser.name)}`;
            } else {
              if (errEl) errEl.innerText = json.error || "Gagal memperbarui profile.";
            }
          } catch (err) {
            console.error("Update profile error:", err);
            if (errEl) errEl.innerText = "Terjadi kesalahan koneksi.";
          } finally {
            if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Simpan"; }
          }
        });
      }

      // Hapus Akun — sembunyikan untuk admin
      const btnDelete = document.querySelector(".btn-delete");
      if (btnDelete) {
        const storedForRole = localStorage.getItem("user");
        const roleCheck = storedForRole ? JSON.parse(storedForRole) : null;
        if (roleCheck && roleCheck.role === "admin") {
          btnDelete.style.display = "none";
        }

        btnDelete.addEventListener("click", async (e) => {
          e.preventDefault();
          const errEl = document.getElementById("errorMsg");
          if (errEl) { errEl.style.color = "red"; errEl.innerText = ""; }

          const storedUser = localStorage.getItem("user");
          const currentUser = storedUser ? JSON.parse(storedUser) : null;
          if (!currentUser) {
            window.location.href = "/login";
            return;
          }

          const confirmed = window.confirm(
            `Hapus akun "${currentUser.name}"?\nSemua data riwayat deteksi akan ikut terhapus dan tidak dapat dikembalikan.`
          );
          if (!confirmed) return;

          if (btnDelete) { btnDelete.disabled = true; btnDelete.textContent = "Menghapus..."; }

          try {
            const res = await fetch(`/api/profile/${currentUser.role}/${currentUser.id}`, {
              method: "DELETE",
            });

            const json = await res.json();

            if (res.ok) {
              localStorage.clear();
              sessionStorage.clear();
              window.location.replace("/login");
            } else {
              if (errEl) errEl.innerText = json.error || "Gagal menghapus akun.";
              if (btnDelete) { btnDelete.disabled = false; btnDelete.textContent = "Hapus Akun"; }
            }
          } catch (err) {
            console.error("Delete profile error:", err);
            if (errEl) errEl.innerText = "Terjadi kesalahan koneksi.";
            if (btnDelete) { btnDelete.disabled = false; btnDelete.textContent = "Hapus Akun"; }
          }
        });
      }
    }
  }

  function navbarRight() {
    const storage = localStorage.getItem("user");
    if (!storage) {
      if (
        window.location.pathname === "/" ||
        window.location.pathname === "/guide"
      ) {
        const topRight = document.querySelector(".top-menu-right");
        const topMenu = document.querySelector(".top-menu");

        if (topRight) topRight.style.display = "none";

        if (topMenu) {
          const div = document.createElement("div");

          div.innerHTML = `
          <div class="top-menu-btn-login">
            <a class="login-button" href="/login">Login</a>
          </div>
        `;

          topMenu.appendChild(div);
        }
      }
      return;
    }
  }

  navbarProfile();
  navbarProfileHandler();
  navbarRight();
  logout();
});
