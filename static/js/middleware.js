document.addEventListener("DOMContentLoaded", () => {
  const storage = localStorage.getItem("user");

  if (!storage) {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/login";
    return;
  }

  const dataUser = JSON.parse(storage);

  if (!dataUser || !dataUser.id) {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/login";
  }
});
