document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".bottom-nav-button");

  const currentPath = window.location.pathname;

  // Set active saat load
  buttons.forEach((btn) => {
    const url = btn.getAttribute("data-url");

    if (currentPath === url || currentPath.startsWith(url + "/")) {
      btn.classList.add("active");
    }

    btn.addEventListener("click", (e) => {
      if (currentPath === url || currentPath.startsWith(url + "/")) {
        e.preventDefault();
        return;
      }

      if (btn.classList.contains("logout")) {
        localStorage.clear();
        sessionStorage.clear();

        window.location.replace("/login");
        return;
      }

      window.location.href = url;
    });
  });
});
