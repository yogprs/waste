document.addEventListener("DOMContentLoaded", () => {
  // Interaction Menu (Sidebar)
  function sideBarMenu() {
    const links = document.querySelectorAll(".sidebar-menu");
    const currentPage = window.location.pathname;

    links.forEach((link) => {
      const path = link.getAttribute("data-href");

      if (path === currentPage) {
        link.classList.add("active");
      }

      // trigger redirect
      link.addEventListener("click", (e) => {
        if (path === currentPage) {
          e.preventDefault(); // stop action
          return;
        }

        window.location.href = path;
      });
    });
  }

  // Data Profile (Sidebar)
  function sideBarProfile() {
    const nameUser = document.getElementById("user-name");
    const email = document.getElementById("email");
    const image = document.getElementById("image-user");

    const storage = localStorage.getItem("user");

    if (!storage) {
      localStorage.clear();
      sessionStorage.clear();
      window.location.href = "/login";
      return;
    }

    const data = JSON.parse(storage);
    if (!data) return;

    if (nameUser) nameUser.textContent = data.name || "-";
    if (email) email.textContent = data.email || "-";
    if (image) image.src = `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(data.name || "?")}`;
  }

  function userProfileHandler() {
    const sidebarUser = document.querySelector(".sidebar-user");
    const modal = document.getElementById("profile-modal");

    // Jika tidak ada sidebar-user atau modal, skip
    if (!sidebarUser || !modal) return;

    const closeModal = document.getElementById("close-modal");
    const nameInput = document.getElementById("profile-name");
    const emailInput = document.getElementById("profile-email");
    const passwordInput = document.getElementById("password");

    function truncateText(text, maxLength) {
      if (!text) return "";
      return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
    }

    function openProfileModal() {
      const storage = localStorage.getItem("user");
      const user = storage ? JSON.parse(storage) : null;
      modal.classList.add("active");

      if (user) {
        if (nameInput) nameInput.value = user.name || "";
        if (emailInput) emailInput.value = user.email || "";
        if (passwordInput) passwordInput.value = "";
      }

      const errEl = document.getElementById("errorMsg");
      if (errEl) errEl.innerText = "";
    }

    // Klik profile di sidebar -> buka modal & isi field
    sidebarUser.addEventListener("click", () => {
      openProfileModal();
    });

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

        const submitBtn = profileForm.querySelector(".btn-save");
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
            const updatedUser = {
              ...currentUser,
              name: json.data?.name || nameVal,
              email: json.data?.email || emailVal,
            };
            localStorage.setItem("user", JSON.stringify(updatedUser));

            if (errEl) { errEl.style.color = "green"; errEl.innerText = "Profile berhasil diperbarui."; }

            // Refresh tampilan sidebar
            const sidebarName = document.getElementById("user-name");
            const sidebarEmail = document.getElementById("email");
            const sidebarImg = document.getElementById("image-user");
            if (sidebarName) sidebarName.textContent = updatedUser.name;
            if (sidebarEmail) sidebarEmail.textContent = updatedUser.email;
            if (sidebarImg) sidebarImg.src = `https://api.dicebear.com/9.x/initials/svg?seed=${encodeURIComponent(updatedUser.name)}`;

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

        btnDelete.disabled = true;
        btnDelete.textContent = "Menghapus...";

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
            btnDelete.disabled = false;
            btnDelete.textContent = "Hapus Akun";
          }
        } catch (err) {
          console.error("Delete profile error:", err);
          if (errEl) errEl.innerText = "Terjadi kesalahan koneksi.";
          btnDelete.disabled = false;
          btnDelete.textContent = "Hapus Akun";
        }
      });
    }
  }

  // Kelola User — hanya tampil jika role === "admin"
  function adminUserManagement() {
    const storage = localStorage.getItem("user");
    const user = storage ? JSON.parse(storage) : null;
    if (!user || user.role !== "admin") return;

    // Tampilkan tombol Kelola User di sidebar (id="add-user-btn")
    const addUserBtn = document.getElementById("add-user-btn");
    if (addUserBtn) addUserBtn.style.display = "flex";
  }

  function inputListener() {
    const inputs = document.querySelectorAll(
      "#profile-name, #profile-email, #password",
    );
    inputs.forEach((input) => {
      input.addEventListener("input", () => {
        const errEl = document.getElementById("errorMsg");
        if (errEl) errEl.innerText = "";
      });
    });
  }

  function logout() {
    const logoutElement = document.querySelector(".logout");
    if (!logoutElement) return;

    logoutElement.addEventListener("click", () => {
      localStorage.clear();
      sessionStorage.clear();

      window.location.href = "/";
    });
  }

  sideBarMenu();
  sideBarProfile();
  userProfileHandler();
  adminUserManagement();
  inputListener();
  logout();
});
