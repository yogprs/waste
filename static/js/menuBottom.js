document.addEventListener("DOMContentLoaded", () => {
  const storage = localStorage.getItem("user");
  const dataUser = storage ? JSON.parse(storage) : null;
  const isAdmin = dataUser && dataUser.role === "admin";

  // Jika admin → ganti tombol Logout di bottom nav menjadi Kelola User
  if (isAdmin) {
    const logoutBtn = document.querySelector(".bottom-nav .bottom-nav-button.logout");
    if (logoutBtn) {
      logoutBtn.classList.remove("logout");
      logoutBtn.setAttribute("data-url", "/users");
      logoutBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
          <path fill="currentColor" d="M15 14c-2.67 0-8 1.33-8 4v2h16v-2c0-2.67-5.33-4-8-4m-9-4V7H4v3H1v2h3v3h2v-3h3v-2m6 2a4 4 0 0 0 0-8a4 4 0 0 0 0 8"/>
        </svg>
        <span class="bottom-nav-text">Kelola User</span>`;
    }
  }

  const buttons = document.querySelectorAll(".bottom-nav-button");
  const currentPath = window.location.pathname;

  // Set active saat load
  buttons.forEach((btn) => {
    const url = btn.getAttribute("data-url");

    if (url && (currentPath === url || currentPath.startsWith(url + "/"))) {
      btn.classList.add("active");
    }

    btn.addEventListener("click", (e) => {
      const url = btn.getAttribute("data-url");

      if (url && (currentPath === url || currentPath.startsWith(url + "/"))) {
        e.preventDefault();
        return;
      }

      if (btn.classList.contains("logout")) {
        localStorage.clear();
        sessionStorage.clear();
        window.location.replace("/login");
        return;
      }

      if (url) window.location.href = url;
    });
  });
});
