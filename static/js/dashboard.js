document.addEventListener("DOMContentLoaded", () => {
  const storageLocal = localStorage.getItem("user");
  const dataUser = JSON.parse(storageLocal);
  const id_user = dataUser.id;

  let currentPage = 1;
  let limit = 5;

  let currentSortBy = "created_at";
  let currentOrder = "desc";

  function greetings() {
    const storage = localStorage.getItem("user");
    const greetingEl = document.getElementById("greeting");

    if (!storage) return;

    const data = JSON.parse(storage);
    const nameUser = data.name;

    const hour = new Date().getHours(); // ambil jam (0 - 23)
    let greetingText = "";

    if (hour >= 5 && hour < 12) {
      greetingText = "Pagi";
    } else if (hour >= 12 && hour < 15) {
      greetingText = "Siang";
    } else if (hour >= 15 && hour < 18) {
      greetingText = "Sore";
    } else {
      greetingText = "Malam";
    }

    greetingEl.innerText = `Selamat ${greetingText}, ${nameUser}`;
  }

  function liveScan() {
    const identifyButton = document.getElementById("identify-button");

    identifyButton.addEventListener("click", () => {
      window.location.href = "/detection/live";
    });
  }

  function viewAllHandle() {
    const viewAll = document.getElementById("view-all");

    viewAll.addEventListener("click", () => {
      window.location.href = "/history";
    });
  }

  async function getRecentScan() {
    let url = `/api/history/${id_user}?page=${currentPage}&limit=${limit}&sort_by=${currentSortBy}&order=${currentOrder}`;

    const res = await fetch(url);
    const result = await res.json();

    renderRecentScan(result.data);
  }

  function renderRecentScan(data) {
    const recentScanTable = document.getElementById("recent-scans-table");

    recentScanTable.innerHTML = "";

    if (!data.length) {
      recentScanTable.innerHTML = `
        <div style="display: flex; align-items: center; width: 100%; justify-content: center;">
          <p style="font-size: 18px; font-weight: 700;">Tidak ada data</p>
        </div>
      `;
      return;
    }

    data.forEach((item) => {
      const div = document.createElement("div");
      div.className = "recent-scans-data";
      div.dataset.id = item.id;

      div.innerHTML = `
      <div class="recent-scans-image-wrap">
        <img alt="image-waste" class="recent-scans-image" src="${item.image}" />
        <div class="prev-img-icon-wrap">
          <span class="prev-img-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 9a3 3 0 0 0-3 3a3 3 0 0 0 3 3a3 3 0 0 0 3-3a3 3 0 0 0-3-3m0 8a5 5 0 0 1-5-5a5 5 0 0 1 5-5a5 5 0 0 1 5 5a5 5 0 0 1-5 5m0-12.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5"/></svg>
          </span>
        </div>
      </div>
      <div class="recents-scans-detail">
        <h4 class="scans-type">${item.label}</h4>
        <div class="scans-info">
          <span class="scans-accuracy">${item.accuracy}%</span>
          <span class="scans-time">${new Date(item.created_at).toLocaleString()}</span>
        </div>
      </div>
    `;

      //   // event klik gambar
      //   const img = div.querySelector(".recent-scans-image");
      //   img.addEventListener("click", () => {
      //     const modal = document.getElementById("image-preview-modal");
      //     const previewImg = document.getElementById("preview-image");

      //     previewImg.src = item.image;
      //     modal.classList.add("active");
      //   });

      const img = div.querySelector(".recent-scans-image");
      const icon = div.querySelector(".prev-img-icon");

      function openPreview() {
        const modal = document.getElementById("image-preview-modal");
        const previewImg = document.getElementById("preview-image");

        previewImg.src = item.image;
        modal.classList.add("active");
      }

      img.addEventListener("click", openPreview);

      icon.addEventListener("click", (e) => {
        e.stopPropagation();
        openPreview();
      });

      recentScanTable.appendChild(div);
    });

    document
      .getElementById("close-image-preview")
      .addEventListener("click", () => {
        document
          .getElementById("image-preview-modal")
          .classList.remove("active");
      });

    // klik luar modal = close
    window.addEventListener("click", (e) => {
      const modal = document.getElementById("image-preview-modal");
      if (e.target === modal) {
        modal.classList.remove("active");
      }
    });
  }

  getRecentScan();
  greetings();
  liveScan();
  viewAllHandle();
});
