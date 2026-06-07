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
    }

    const data = JSON.parse(storage);
    nameUser.textContent = data.name;
    email.textContent = data.email;
    image.src = `https://api.dicebear.com/9.x/initials/svg?seed=${data.name}`;
  }

  function userProfileHandler() {
    const sidebarUser = document.querySelector(".sidebar-user");
    const modal = document.getElementById("profile-modal");
    const closeModal = document.getElementById("close-modal");

    const nameInput = document.getElementById("profile-name");
    const emailInput = document.getElementById("profile-email");
    const passwordInput = document.getElementById("password");

    // Ambil data user dari localStorage
    const storage = localStorage.getItem("user");
    const user = storage ? JSON.parse(storage) : null;

    // Klik profile -> buka modal
    sidebarUser.addEventListener("click", () => {
      const storage = localStorage.getItem("user");
      const user = storage ? JSON.parse(storage) : null;
      modal.classList.add("active");

      if (user) {
        nameInput.value = user.name || "";
        emailInput.value = user.email || "";
        passwordInput.value = "";
      }
    });

    // Tutup modal
    closeModal.addEventListener("click", () => {
      modal.classList.remove("active");
    });

    // Klik luar modal -> tutup
    window.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("active");
      }
    });

    // Submit form
    document
      .getElementById("profile-form")
      .addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!nameInput.value) {
          document.getElementById("errorMsg").innerText = "Nama wajib di isi!";
          return;
        }

        if (!emailInput.value) {
          document.getElementById("errorMsg").innerText = "Email wajib di isi!";
          return;
        }

        const updatedUser = {
          ...user,
          name: nameInput.value,
          email: emailInput.value,
        };

        if (passwordInput.value && passwordInput.value.length < 8) {
          document.getElementById("errorMsg").innerText =
            "Password harus lebih dari 8 karakter!";
          return;
        } else {
          updatedUser.password = passwordInput.value;
        }

        try {
          const response = await fetch(`/api/profile/${user.id}`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ updatedUser }),
          });

          const result = await response.json();

          if (response.ok) {
            nameInput.value = "";
            emailInput.value = "";
            passwordInput.value = "";
            localStorage.setItem(
              "user",
              JSON.stringify({
                id: result.data.id,
                name: updatedUser.name,
                email: updatedUser.email,
              }),
            );
            nameInput.value = updatedUser.name || "";
            emailInput.value = updatedUser.email || "";

            alert("Profile berhasil diperbarui!");

            passwordInput.value = "";

            modal.classList.remove("active");
            sideBarProfile();
          } else {
            document.getElementById("errorMsg").innerText = result.error;
          }
        } catch (err) {
          console.error(err);
          alert("Terjadi error");
        }
      });

    // Hapus AKun
    document
      .querySelector(".btn-delete")
      .addEventListener("click", async (e) => {
        e.preventDefault();

        try {
          const response = await fetch(`/api/profile/${user.id}`, {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
            },
          });

          const result = await response.json();

          if (response.ok) {
            nameInput.value = "";
            emailInput.value = "";
            passwordInput.value = "";

            alert("Akun berhasil dihapus!");

            modal.classList.remove("active");
            sideBarProfile();

            localStorage.clear();
            sessionStorage.clear();
            window.location.href = "/";
          } else {
            document.getElementById("errorMsg").innerText = result.error;
          }
        } catch (err) {
          console.error(err);
          alert("Terjadi error");
        }
      });
  }

  function inputListener() {
    const inputs = document.querySelectorAll(
      "#profile-name, #email, #password",
    );
    inputs.forEach((input) => {
      input.addEventListener("input", () => {
        document.getElementById("errorMsg").innerText = "";
      });
    });
  }

  function logout() {
    const logoutElement = document.querySelector(".logout");

    logoutElement.addEventListener("click", () => {
      localStorage.clear();
      sessionStorage.clear();

      window.location.href = "/";
    });
  }

  sideBarMenu();
  sideBarProfile();
  userProfileHandler();
  inputListener();
  logout();
});
