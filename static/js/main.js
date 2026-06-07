document.addEventListener("DOMContentLoaded", () => {
  const buttonTry = document.querySelector(".button-try");
  const buttonLearn = document.querySelector(".button-learn");

  buttonTry.addEventListener("click", () => {
    window.location.href = "/detection";
  });

  buttonLearn.addEventListener("click", () => {
    window.location.href = "/guide";
  });

  function setBottomNavMenu() {
    const storage = localStorage.getItem("user");

    const user = JSON.parse(storage);

    if (user && user.id) {
      const bottomNav = document.getElementById("bottomNav");
      const buttonLogin = document.querySelector(".bottom-nav-button.login");

      // bottomNav.innerHTML = "";

      const button = document.createElement("button");
      button.className = "bottom-nav-button logout";

      button.innerHTML = `
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          viewBox="0 0 24 24"
        >
          <path
            fill="currentColor"
            d="M5 21q-.825 0-1.412-.587T3 19V5q0-.825.588-1.412T5 3h7v2H5v14h7v2zm11-4l-1.375-1.45l2.55-2.55H9v-2h8.175l-2.55-2.55L16 7l5 5z"
          />
        </svg>
        <span class="bottom-nav-text">Logout</span>
      `;
      bottomNav.appendChild(button);
      buttonLogin.style.display = "none";
    }
  }

  setBottomNavMenu();
});
