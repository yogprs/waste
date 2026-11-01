/**
 * users.js — Kelola User (Admin Only)
 * Handles: fetch users, add user, edit password, delete user
 */

(function () {
  // ─── State ───────────────────────────────────────────────────────────────
  const storage = localStorage.getItem("user");
  const dataUser = storage ? JSON.parse(storage) : null;

  // Guard: hanya admin yang boleh akses halaman ini
  if (!dataUser || dataUser.role !== "admin") {
    window.location.href = "/login";
    return;
  }

  const adminId = dataUser.id;

  let currentPage = 1;
  let currentRole = "all";
  let currentSearch = "";
  let searchTimeout = null;
  let editingUser = null; // { id, role, nama }

  // ─── DOM Refs ────────────────────────────────────────────────────────────
  const tableBody = document.getElementById("users-table-body");
  const paginationEl = document.getElementById("users-pagination");
  const totalInfoEl = document.getElementById("users-total-info");
  const searchInput = document.getElementById("users-search");
  const filterChips = document.querySelectorAll(".filter-chip");

  // Modal: Tambah User
  const addUserModal = document.getElementById("add-user-modal");
  const closeAddUserModalBtn = document.getElementById("close-add-user-modal");
  const addUserForm = document.getElementById("add-user-form");
  const addUserErrorEl = document.getElementById("addUserError");
  const btnOpenAddUser = document.getElementById("btn-open-add-user");

  // Modal: Edit Password
  const editPasswordModal = document.getElementById("edit-password-modal");
  const closeEditPasswordBtn = document.getElementById("close-edit-password-modal");
  const editPasswordForm = document.getElementById("edit-password-form");
  const editPasswordErrorEl = document.getElementById("editPasswordError");
  const editPasswordUserName = document.getElementById("edit-password-user-name");
  const newPasswordInput = document.getElementById("new-password-input");

  // ─── Fetch Users ─────────────────────────────────────────────────────────
  async function fetchUsers(page, role, search) {
    tableBody.innerHTML = `<tr><td colspan="4"><div class="users-empty">Memuat data...</div></td></tr>`;
    paginationEl.innerHTML = "";
    totalInfoEl.textContent = "";

    try {
      const params = new URLSearchParams({
        id_admin: adminId,
        role: role,
        page: page,
        limit: 10,
      });
      if (search) params.set("search", search);

      const res = await fetch(`/api/users?${params.toString()}`);
      const json = await res.json();

      if (!res.ok) {
        tableBody.innerHTML = `<tr><td colspan="4"><div class="users-empty">${json.error || "Gagal memuat data."}</div></td></tr>`;
        return;
      }

      renderTable(json.data);
      renderPagination(json.total, json.page, json.total_page);
      totalInfoEl.textContent =
        json.total > 0
          ? `Menampilkan ${json.data.length} dari ${json.total} pengguna`
          : "";
    } catch (err) {
      console.error("fetchUsers error:", err);
      tableBody.innerHTML = `<tr><td colspan="4"><div class="users-empty">Terjadi kesalahan koneksi.</div></td></tr>`;
    }
  }

  // ─── Render Table ─────────────────────────────────────────────────────────
  function renderTable(data) {
    if (!data || data.length === 0) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="4">
            <div class="users-empty">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24">
                <path fill="currentColor" d="M12 2a5 5 0 1 1 0 10A5 5 0 0 1 12 2m0 12c5.33 0 8 2.67 8 4v2H4v-2c0-1.33 2.67-4 8-4z"/>
              </svg>
              Tidak ada pengguna ditemukan.
            </div>
          </td>
        </tr>`;
      return;
    }

    tableBody.innerHTML = data
      .map(
        (u) => `
      <tr>
        <td data-label="Nama">${escapeHtml(u.nama)}</td>
        <td data-label="Email">${escapeHtml(u.email)}</td>
        <td data-label="Role"><span class="role-badge ${u.role}">${capitalize(u.role)}</span></td>
        <td data-label="">
          <div class="table-actions">
            <button class="btn-edit-pass" data-id="${u.id}" data-role="${u.role}" data-nama="${escapeHtml(u.nama)}">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24">
                <path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2m-6 9c-1.1 0-2-.9-2-2s.9-2 2-2s2 .9 2 2s-.9 2-2 2m3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1s3.1 1.39 3.1 3.1v2z"/>
              </svg>
              Ubah Password
            </button>
            <button class="btn-delete-user" data-id="${u.id}" data-role="${u.role}" data-nama="${escapeHtml(u.nama)}">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24">
                <path fill="currentColor" d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6zM19 4h-3.5l-1-1h-5l-1 1H5v2h14z"/>
              </svg>
              Hapus
            </button>
          </div>
        </td>
      </tr>`
      )
      .join("");

    // Attach action listeners
    tableBody.querySelectorAll(".btn-edit-pass").forEach((btn) => {
      btn.addEventListener("click", () => {
        openEditPassword({ id: btn.dataset.id, role: btn.dataset.role, nama: btn.dataset.nama });
      });
    });
    tableBody.querySelectorAll(".btn-delete-user").forEach((btn) => {
      btn.addEventListener("click", () => {
        deleteUser(btn.dataset.role, btn.dataset.id, btn.dataset.nama);
      });
    });
  }

  // ─── Render Pagination ────────────────────────────────────────────────────
  function renderPagination(total, page, totalPage) {
    paginationEl.innerHTML = "";
    if (totalPage <= 1) return;

    const prevBtn = document.createElement("button");
    prevBtn.textContent = "‹ Prev";
    prevBtn.disabled = page <= 1;
    prevBtn.addEventListener("click", () => {
      currentPage = page - 1;
      fetchUsers(currentPage, currentRole, currentSearch);
    });
    paginationEl.appendChild(prevBtn);

    // Page number buttons (max 5 shown)
    const start = Math.max(1, page - 2);
    const end = Math.min(totalPage, page + 2);
    for (let i = start; i <= end; i++) {
      const btn = document.createElement("button");
      btn.textContent = i;
      if (i === page) btn.classList.add("active");
      btn.addEventListener("click", () => {
        currentPage = i;
        fetchUsers(currentPage, currentRole, currentSearch);
      });
      paginationEl.appendChild(btn);
    }

    const nextBtn = document.createElement("button");
    nextBtn.textContent = "Next ›";
    nextBtn.disabled = page >= totalPage;
    nextBtn.addEventListener("click", () => {
      currentPage = page + 1;
      fetchUsers(currentPage, currentRole, currentSearch);
    });
    paginationEl.appendChild(nextBtn);
  }

  // ─── Delete User ──────────────────────────────────────────────────────────
  async function deleteUser(role, id, nama) {
    if (!window.confirm(`Hapus pengguna "${nama}" (${capitalize(role)})?\nTindakan ini tidak dapat dibatalkan.`)) return;

    try {
      const res = await fetch(`/api/users/${role}/${id}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_admin: adminId }),
      });
      const json = await res.json();
      if (res.ok) {
        alert(`Pengguna "${nama}" berhasil dihapus.`);
        fetchUsers(currentPage, currentRole, currentSearch);
      } else {
        alert(json.error || "Gagal menghapus pengguna.");
      }
    } catch (err) {
      console.error("deleteUser error:", err);
      alert("Terjadi kesalahan saat menghapus pengguna.");
    }
  }

  // ─── Edit Password Modal ──────────────────────────────────────────────────
  function openEditPassword(user) {
    editingUser = user;
    editPasswordUserName.textContent = `Pengguna: ${user.nama} (${capitalize(user.role)})`;
    newPasswordInput.value = "";
    editPasswordErrorEl.textContent = "";
    editPasswordModal.classList.add("active");
    newPasswordInput.focus();
  }

  closeEditPasswordBtn.addEventListener("click", () => {
    editPasswordModal.classList.remove("active");
  });

  window.addEventListener("click", (e) => {
    if (e.target === editPasswordModal) editPasswordModal.classList.remove("active");
    if (e.target === addUserModal) addUserModal.classList.remove("active");
  });

  editPasswordForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    editPasswordErrorEl.textContent = "";
    const newPw = newPasswordInput.value;

    if (!newPw || newPw.length < 8) {
      editPasswordErrorEl.textContent = "Password minimal 8 karakter.";
      return;
    }

    const submitBtn = editPasswordForm.querySelector("button[type='submit']");
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Menyimpan..."; }

    try {
      const res = await fetch(`/api/users/${editingUser.role}/${editingUser.id}/password`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_admin: adminId, new_password: newPw }),
      });
      const json = await res.json();
      if (res.ok) {
        alert(`Password "${editingUser.nama}" berhasil diperbarui.`);
        editPasswordModal.classList.remove("active");
      } else {
        editPasswordErrorEl.textContent = json.error || "Gagal memperbarui password.";
      }
    } catch (err) {
      console.error("updatePassword error:", err);
      editPasswordErrorEl.textContent = "Terjadi kesalahan koneksi.";
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Simpan Password"; }
    }
  });

  // ─── Add User Modal ───────────────────────────────────────────────────────
  btnOpenAddUser.addEventListener("click", () => {
    addUserErrorEl.textContent = "";
    addUserForm.reset();
    addUserModal.classList.add("active");
  });

  closeAddUserModalBtn.addEventListener("click", () => {
    addUserModal.classList.remove("active");
  });

  addUserForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    addUserErrorEl.textContent = "";

    const newName = document.getElementById("new-user-name")?.value?.trim();
    const newEmail = document.getElementById("new-user-email")?.value?.trim();
    const newPassword = document.getElementById("new-user-password")?.value;
    const roleRadio = document.querySelector("input[name='new-user-role']:checked");
    const newRole = roleRadio ? roleRadio.value : null;

    if (!newName || !newEmail || !newPassword || !newRole) {
      addUserErrorEl.textContent = "Semua field wajib diisi.";
      return;
    }
    if (newPassword.length < 8) {
      addUserErrorEl.textContent = "Password minimal 8 karakter.";
      return;
    }

    const submitBtn = addUserForm.querySelector("button[type='submit']");
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Menyimpan..."; }

    try {
      const res = await fetch("/api/create/user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newName,
          email: newEmail,
          password: newPassword,
          role: newRole,
          id_admin: adminId,
        }),
      });
      const json = await res.json();
      if (res.ok) {
        alert(`Akun ${capitalize(newRole)} atas nama "${newName}" berhasil dibuat!`);
        addUserModal.classList.remove("active");
        addUserForm.reset();
        currentPage = 1;
        fetchUsers(currentPage, currentRole, currentSearch);
      } else {
        addUserErrorEl.textContent = json.error || "Gagal membuat akun.";
      }
    } catch (err) {
      console.error("addUser error:", err);
      addUserErrorEl.textContent = "Terjadi kesalahan koneksi.";
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = "Buat Akun"; }
    }
  });

  // ─── Filter Chips ─────────────────────────────────────────────────────────
  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      filterChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      currentRole = chip.dataset.role;
      currentPage = 1;
      fetchUsers(currentPage, currentRole, currentSearch);
    });
  });

  // ─── Search (debounced) ───────────────────────────────────────────────────
  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      currentSearch = searchInput.value.trim();
      currentPage = 1;
      fetchUsers(currentPage, currentRole, currentSearch);
    }, 400);
  });

  // ─── Helpers ─────────────────────────────────────────────────────────────
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  // ─── Init ─────────────────────────────────────────────────────────────────
  fetchUsers(currentPage, currentRole, currentSearch);
})();
