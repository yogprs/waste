document.addEventListener("DOMContentLoaded", () => {
  const storage = localStorage.getItem("user");
  const dataUser = JSON.parse(storage);

  if (!dataUser.id) {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/login";
  }
});
