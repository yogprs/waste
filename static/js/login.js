document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll(
    "#name, #email, #password, #confirm",
  );

  inputs.forEach((input) => {
    input.addEventListener("input", () => {
      document.getElementById("errorMsg").innerText = "";
    });
  });

  document
    .getElementById("loginForm")
    .addEventListener("submit", async function (e) {
      e.preventDefault(); //  supaya tidak reload

      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;

      try {
        const response = await fetch("/api/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email,
            password: password,
          }),
        });

        const result = await response.json();
        if (response.ok) {
          localStorage.setItem("user", JSON.stringify(result.user));
          alert("Login berhasil!");
          window.location.href = "/dashboard";
        } else {
          //   alert(result.error);
          document.getElementById("errorMsg").innerText = result.error;
        }
      } catch (err) {
        console.error(err);
        alert("Terjadi error");
      }
    });

  function setBottomNavMenu() {
    const storage = localStorage.getItem("user");

    const user = JSON.parse(storage);

    if (user.id) {
      window.location.href = "/dashboard";
    }
    // if (user.id) {
    //   const bottomNav = document.getElementById("bottomNav");
    //   bottomNav.innerHTML = "";

    //   const button = document.createElement("button");
    //   button.className = "bottom-nav-button logout";

    //   button.innerHTML = `
    //     <svg
    //       xmlns="http://www.w3.org/2000/svg"
    //       width="24"
    //       height="24"
    //       viewBox="0 0 24 24"
    //     >
    //       <path
    //         fill="currentColor"
    //         d="M5 21q-.825 0-1.412-.587T3 19V5q0-.825.588-1.412T5 3h7v2H5v14h7v2zm11-4l-1.375-1.45l2.55-2.55H9v-2h8.175l-2.55-2.55L16 7l5 5z"
    //       />
    //     </svg>
    //     <span class="bottom-nav-text">Logout</span>
    //   `;
    // }
  }

  setBottomNavMenu();
});
