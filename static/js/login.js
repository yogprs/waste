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
    if (!storage) return;

    const user = JSON.parse(storage);

    if (user && user.id) {
      window.location.href = "/dashboard";
    }
  }

  setBottomNavMenu();
});
