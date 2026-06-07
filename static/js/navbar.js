document.addEventListener("DOMContentLoaded", () => {
  function truncateText(text, maxLength) {
    if (text.length > maxLength) {
      return text.substring(0, maxLength) + "...";
    }
    return text;
  }

  function logout() {
    const logoutElement = document.querySelector(".nav-menu-item.logout");

    logoutElement.addEventListener("click", () => {
      localStorage.clear();
      sessionStorage.clear();

      window.location.href = "/";
    });
  }

  function navbarProfile() {
    const nameUser = document.getElementById("nav-user-name");
    const email = document.getElementById("nav-email");
    const image = document.getElementById("nav-image-user");

    const storage = localStorage.getItem("user");

    const data = JSON.parse(storage);
    if (!data) return;
    nameUser.textContent = truncateText(data.name, 10);
    email.textContent = truncateText(data.email, 10);
    image.src = `https://api.dicebear.com/9.x/initials/svg?seed=${data.name}`;
  }

  function navbarProfileHandler() {
    const trigger = document.getElementById("nav-profile-trigger");
    const menu = document.getElementById("nav-profile-menu");
    const openProfile = document.getElementById("open-profile");
    const dashboardProfile = document.getElementById("dashboard-profile");
    const sidebarUser = document.querySelector(".sidebar-user");
    const modal = document.getElementById("profile-modal");

    // Ambil data user dari localStorage
    const storage = localStorage.getItem("user");
    const user = storage ? JSON.parse(storage) : null;

    if (!trigger || !menu) return;

    let isOpen = false;

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();

      isOpen = !isOpen;
      menu.classList.toggle("active", isOpen);
    });

    document.addEventListener("click", (e) => {
      if (
        !menu.contains(e.target) &&
        !e.target.closest("#nav-profile-trigger")
      ) {
        menu.classList.remove("active");
        isOpen = false;
      }
    });

    menu.addEventListener("click", (e) => {
      e.stopPropagation();
    });

    if (openProfile) {
      openProfile.addEventListener("click", () => {
        document.getElementById("profile-modal").classList.add("active");

        const storage = localStorage.getItem("user");
        const user = storage ? JSON.parse(storage) : null;
        if (user) {
          const nameInput = document.getElementById("profile-name");
          const emailInput = document.getElementById("profile-email");
          const passwordInput = document.getElementById("password");
          if (nameInput) nameInput.value = user.name || "";
          if (emailInput) emailInput.value = user.email || "";
          if (passwordInput) passwordInput.value = "";
        }

        menu.classList.remove("active");
        isOpen = false;
      });
    }

    if (dashboardProfile) {
      dashboardProfile.addEventListener("click", () => {
        window.location.href = "/dashboard";
      });
    }

    if (!sidebarUser) {
      const closeModal = document.getElementById("close-modal");
      const nameInput = document.getElementById("profile-name");
      const emailInput = document.getElementById("profile-email");
      const passwordInput = document.getElementById("password");

      // Klik profile -> buka modal
      openProfile.addEventListener("click", () => {
        modal.classList.add("active");

        if (user) {
          const storage = localStorage.getItem("user");
          const user = storage ? JSON.parse(storage) : null;
          nameInput.value = user.name || "";
          emailInput.value = user.email || "";
          passwordInput.value = "";
        }
      });

      // Tutup modal
      if (closeModal) {
        closeModal.addEventListener("click", () => {
          modal.classList.remove("active");
        });
      }

      // Klik luar modal -> tutup
      window.addEventListener("click", (e) => {
        if (!e.target.closest(".modal-content")) {
          modal.classList.remove("active");
        }
      });

      // Submit form
      document
        .getElementById("profile-form")
        .addEventListener("submit", async (e) => {
          e.preventDefault();

          if (!nameInput.value) {
            document.getElementById("errorMsg").innerText =
              "Nama wajib di isi!";
            return;
          }

          if (!emailInput.value) {
            document.getElementById("errorMsg").innerText =
              "Email wajib di isi!";
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
              alert("Profile berhasil diperbarui!");
              modal.classList.remove("active");
              navbarProfile();
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
              navbarProfile();

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
  }

  function navbarRight() {
    const storage = localStorage.getItem("user");

    const data = JSON.parse(storage);
    if (!data) {
      if (
        window.location.pathname === "/" ||
        window.location.pathname === "/guide"
      ) {
        const topRight = document.querySelector(".top-menu-right");
        const topMenu = document.querySelector(".top-menu");

        topRight.style.display = "none";

        const div = document.createElement("div");

        div.innerHTML = `
          <div class="top-menu-btn-login">
            <a class="login-button" href="/login">Login</a>
          </div>
        `;

        topMenu.appendChild(div);
        // top-menu-right
      }
    }
  }

  navbarProfile();
  navbarProfileHandler();
  navbarRight();
  logout();
});
