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
    .getElementById("registerForm")
    .addEventListener("submit", async function (e) {
      e.preventDefault(); //  supaya tidak reload

      const name = document.getElementById("name").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      const confirm = document.getElementById("confirm").value;

      if (password !== confirm) {
        alert("Password tidak sama!");
        return;
      }

      try {
        const response = await fetch("/api/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name,
            email: email,
            password: password,
          }),
        });

        const result = await response.json();

        if (response.ok) {
          alert("Register berhasil!");
          window.location.href = "/login";
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
  }

  setBottomNavMenu();
});
