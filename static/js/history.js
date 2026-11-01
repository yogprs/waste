document.addEventListener("DOMContentLoaded", () => {
  const storageLocal = localStorage.getItem("user");
  const dataUser = JSON.parse(storageLocal);
  const id_user = dataUser.id;
  const user_role = dataUser.role; // ambil role dari localStorage

  let currentPage = 1;
  let limit = 6;

  let currentLabel = "";

  let currentSortBy = "dibuat_pada"; // sesuai nama kolom di API
  let currentOrder = "desc";

  let timeOrder = "desc";
  let accuracyOrder = "desc";

  let isSelectAllGlobal = false;
  let selectedIds = new Set();
  let allLoadedIds = []; // simpan semua ID dari halaman yang sudah di-load

  async function fetchHistory() {
    // URL sesuai endpoint API: /api/history/<user_type>/<id_user>
    let url = `/api/history/${user_role}/${id_user}?page=${currentPage}&limit=${limit}&sort_by=${currentSortBy}&order=${currentOrder}`;

    if (currentLabel) {
      url += `&label=${currentLabel}`;
    }

    const res = await fetch(url);
    const result = await res.json();

    // Simpan semua ID dari data yang di-load di halaman ini
    allLoadedIds = (result.data || []).map((item) => item.id);

    renderHistory(result.data);
    renderPagination(result.total, result.page, result.limit);

    updateSelectionUI();
  }

  function formatNumber(number) {
    return Number.isInteger(number) ? number.toFixed(1) : number.toString();
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function renderHistory(data) {
    const grid = document.getElementById("historyGrid");
    grid.innerHTML = "";

    if (!data.length) {
      grid.innerHTML = `
        <div style="grid-column: span 3 / span 3; align-items: center; width: 100%; justify-content: center;">
          <p style="font-size: 18px; font-weight: 700; text-align: center;">Tidak ada data</p>
        </div>
      `;
      return;
    }

    data.forEach((item) => {
      const div = document.createElement("div");
      div.className = "grid-item";
      div.dataset.id = item.id;

      div.innerHTML = `
        <div class="grid-item-action-check">
          <input class="custom-checkbox grid-item-check" type="checkbox" />
        </div>

        <div class="grid-item-image">
          <img class="grid-image" src="${item.image}" />
          <div class="prev-img-icon-wrap">
            <span class="prev-img-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M12 9a3 3 0 0 0-3 3a3 3 0 0 0 3 3a3 3 0 0 0 3-3a3 3 0 0 0-3-3m0 8a5 5 0 0 1-5-5a5 5 0 0 1 5-5a5 5 0 0 1 5 5a5 5 0 0 1-5 5m0-12.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5"/></svg>
            </span>
          </div>
          <div class="accuracy">${formatNumber(item.accuracy)}%</div>
        </div>

        <div class="grid-item-text-container">
          <div class="grid-item-text-wrap">
            <div class="grid-item-top-info">
              <p class="grid-item-time">
                <span class="grid-item-time-icon">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                  >
                    <path
                      fill="currentColor"
                      d="M5 22q-.825 0-1.412-.587T3 20V6q0-.825.588-1.412T5 4h1V2h2v2h8V2h2v2h1q.825 0 1.413.588T21 6v14q0 .825-.587 1.413T19 22zm0-2h14V10H5z"
                    />
                  </svg>
                </span>
                ${new Date(item.created_at).toLocaleString()}
              </p>
              <span class="grid-item-waste-type ${
                item.label === "Organik" ? "organic" : "non-organic"
              }">
                ${item.label}
              </span>
            </div>
            <div class="grid-item-user-info">
              <div class="grid-item-user-left">
                <span class="grid-item-user-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24">
                    <path fill="currentColor" d="M12 4a4 4 0 0 1 4 4a4 4 0 0 1-4 4a4 4 0 0 1-4-4a4 4 0 0 1 4-4m0 10c4.42 0 8 1.79 8 4v2H4v-2c0-2.21 3.58-4 8-4"/>
                  </svg>
                </span>
                <span class="grid-item-user-name" title="${escapeHtml(item.user_name || 'Pengguna')}">
                  ${escapeHtml(item.user_name || 'Pengguna')}
                </span>
              </div>
              ${item.user_type ? `<span class="grid-item-role-badge ${escapeHtml(item.user_type.toLowerCase())}">${escapeHtml(capitalize(item.user_type))}</span>` : ''}
            </div>
          </div>
        </div>
      `;

      const img = div.querySelector(".grid-image");
      const itemText = div.querySelector(".grid-item-text-wrap");
      const icon = div.querySelector(".prev-img-icon");

      function openPreview() {
        const modal = document.getElementById("image-preview-modal");
        const previewImg = document.getElementById("preview-image");

        previewImg.src = item.image;
        modal.classList.add("active");
      }

      img.addEventListener("click", openPreview);

      itemText.addEventListener("click", () => {
        sessionStorage.setItem(
          "result-scan",
          JSON.stringify({
            image: item.image,
            label: item.label,
            accuracy: `${formatNumber(item.accuracy)}%`,
            image_url: item.image,
          }),
        );

        window.location.href = "/detection/result";
      });

      icon.addEventListener("click", (e) => {
        e.stopPropagation();
        openPreview();
      });

      grid.appendChild(div);
    });
  }

  document
    .getElementById("close-image-preview")
    .addEventListener("click", () => {
      document.getElementById("image-preview-modal").classList.remove("active");
    });

  // klik luar modal = close
  window.addEventListener("click", (e) => {
    const modal = document.getElementById("image-preview-modal");
    if (e.target === modal) {
      modal.classList.remove("active");
    }
  });

  // update UI selection
  function updateSelectionUI() {
    const items = document.querySelectorAll(".grid-item");
    const checked = document.querySelectorAll(".grid-item-check:checked");
    const selectionControls = document.querySelector(".selection-controls");
    const totalSelectedText = document.querySelector(".total-item-selected");
    const selectAll = document.querySelector(".select-all-label input");

    // highlight
    items.forEach((item) => {
      const cb = item.querySelector(".grid-item-check");
      item.classList.toggle("selected", cb.checked);
    });

    // controls
    if (checked.length > 0 || isSelectAllGlobal) {
      selectionControls.classList.remove("hidden");

      if (isSelectAllGlobal) {
        totalSelectedText.textContent = `Semua item dipilih`;
      } else {
        totalSelectedText.textContent = `${checked.length} item dipilih`;
      }
    } else {
      selectionControls.classList.add("hidden");
    }

    if (selectAll) {
      if (isSelectAllGlobal) {
        selectAll.checked = true;
      } else {
        const all = document.querySelectorAll(".grid-item-check");
        selectAll.checked = all.length > 0 && checked.length === all.length;
      }
    }
  }

  // checkbox global listener
  function checkboxGlobalHandler() {
    document.addEventListener("change", (e) => {
      if (!e.target.matches(".grid-item-check")) return;

      const id = e.target.closest(".grid-item").dataset.id;

      if (e.target.checked) {
        selectedIds.add(id);
      } else {
        selectedIds.delete(id);
        isSelectAllGlobal = false;
      }

      updateSelectionUI();
    });
  }

  async function selectAllHandler() {
    const selectAllCheckbox = document.querySelector(".select-all-label input");
    if (!selectAllCheckbox) return;

    selectAllCheckbox.addEventListener("change", async () => {
      if (selectAllCheckbox.checked) {
        // Gunakan ID dari halaman yang sudah di-load (tidak ada endpoint /ids)
        selectedIds = new Set(allLoadedIds);
        isSelectAllGlobal = true;

        document.querySelectorAll(".grid-item-check").forEach((cb) => {
          cb.checked = true;
        });
      } else {
        selectedIds.clear();
        isSelectAllGlobal = false;

        document.querySelectorAll(".grid-item-check").forEach((cb) => {
          cb.checked = false;
        });
      }

      updateSelectionUI();
    });
  }

  function deleteSelectedHandler() {
    const deleteButton = document.querySelector(".delete-button");
    if (!deleteButton) return;

    deleteButton.addEventListener("click", async () => {
      if (selectedIds.size === 0 && !isSelectAllGlobal) return;

      const confirmMsg = isSelectAllGlobal
        ? "Apakah Anda yakin ingin menghapus SEMUA riwayat deteksi?"
        : `Apakah Anda yakin ingin menghapus ${selectedIds.size} riwayat deteksi yang dipilih?`;

      if (!window.confirm(confirmMsg)) return;

      deleteButton.disabled = true;
      deleteButton.textContent = "Menghapus...";

      try {
        let res;
        if (isSelectAllGlobal) {
          // DELETE ALL — endpoint /api/history (DELETE)
          res = await fetch("/api/history", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_type: user_role,
              id_user,
              label: currentLabel || null,
              delete_all: true,
            }),
          });
        } else {
          // DELETE SELECTED — endpoint /api/history (DELETE)
          res = await fetch("/api/history", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_type: user_role,
              id_user,
              ids: Array.from(selectedIds),
              delete_all: false,
            }),
          });
        }

        const json = await res.json();

        if (!res.ok) {
          alert(json.error || "Gagal menghapus riwayat.");
          return;
        }

        alert(json.message || "Data riwayat berhasil dihapus!");

        // reset state
        resetSelection();
        currentPage = 1;
        fetchHistory();
      } catch (err) {
        console.error("Delete error:", err);
        alert("Terjadi kesalahan saat menghapus riwayat.");
      } finally {
        deleteButton.disabled = false;
        deleteButton.textContent = "Hapus";
      }
    });
  }

  function resetSelection() {
    selectedIds.clear();
    isSelectAllGlobal = false;

    // uncheck select all
    const selectAll = document.querySelector(".select-all-label input");
    if (selectAll) selectAll.checked = false;

    // uncheck semua checkbox di UI
    document.querySelectorAll(".grid-item-check").forEach((cb) => {
      cb.checked = false;
    });

    // hide selection controls
    const selectionControls = document.querySelector(".selection-controls");
    if (selectionControls) {
      selectionControls.classList.add("hidden");
    }
  }

  function renderPagination(total, page, limit) {
    const totalPages = Math.ceil(total / limit);
    const pagination = document.querySelector(".pagination");

    pagination.innerHTML = "";

    if (totalPages <= 1) return;

    const firstSVG = `
    <span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="18"
        height="18"
        viewBox="0 0 24 24"
      >
        <path
          fill="currentColor"
          d="m11 18l-6-6l6-6l1.4 1.4L7.825 12l4.575 4.6zm6.6 0l-6-6l6-6L19 7.4L14.425 12L19 16.6z"
        /></svg>
    </span>`;

    const prevSVG = `
    <span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="18"
        height="18"
        viewBox="0 0 24 24"
      >
        <path
          fill="currentColor"
          d="m14 18l-6-6l6-6l1.4 1.4l-4.6 4.6l4.6 4.6z"
        /></svg>
    </span>`;

    const nextSVG = `
    <span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="18"
        height="18"
        viewBox="0 0 24 24"
      >
        <path
          fill="currentColor"
          d="M12.6 12L8 7.4L9.4 6l6 6l-6 6L8 16.6z"
        /></svg>
    </span>`;

    const lastSVG = `
    <span>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="18"
        height="18"
        viewBox="0 0 24 24"
      >
        <path
          fill="currentColor"
          d="M9.575 12L5 7.4L6.4 6l6 6l-6 6L5 16.6zm6.6 0L11.6 7.4L13 6l6 6l-6 6l-1.4-1.4z"
        /></svg>
    </span>`;

    // ======================
    // HELPER
    // ======================
    const createButton = (html, onClick, disabled = false) => {
      const btn = document.createElement("button");
      btn.className = "button-pagination";
      btn.innerHTML = html;

      if (disabled) {
        btn.disabled = true;
        btn.classList.add("disabled");
      } else {
        btn.onclick = onClick;
      }

      return btn;
    };

    const createPage = (i) => {
      const btn = document.createElement("button");
      btn.className = "button-page" + (i === page ? " active" : "");
      btn.innerText = i;

      if (i !== page) {
        btn.onclick = () => {
          currentPage = i;
          resetSelection();
          fetchHistory();
        };
      }

      return btn;
    };

    const createDot = () => {
      const span = document.createElement("span");
      span.className = "dot";
      span.textContent = "...";
      return span;
    };

    // ======================
    // ARROW
    // ======================
    pagination.appendChild(
      createButton(
        firstSVG,
        () => {
          currentPage = 1;
          resetSelection();
          fetchHistory();
        },
        page === 1,
      ),
    );

    pagination.appendChild(
      createButton(
        prevSVG,
        () => {
          currentPage--;
          resetSelection();
          fetchHistory();
        },
        page === 1,
      ),
    );

    // ======================
    // PAGE LOGIC
    // ======================
    let start = Math.max(1, page - 2);
    let end = Math.min(totalPages, page + 2);

    // Page 1
    if (start > 1) {
      pagination.appendChild(createPage(1));

      if (start > 2) {
        pagination.appendChild(createDot());
      }
    }

    // Middle
    for (let i = start; i <= end; i++) {
      pagination.appendChild(createPage(i));
    }

    // Last Page
    if (end < totalPages) {
      if (end < totalPages - 1) {
        pagination.appendChild(createDot());
      }

      pagination.appendChild(createPage(totalPages)); // last page setelah dot
    }

    // ======================
    // NEXT
    // ======================
    pagination.appendChild(
      createButton(
        nextSVG,
        () => {
          currentPage++;
          resetSelection();
          fetchHistory();
        },
        page === totalPages,
      ),
    );

    pagination.appendChild(
      createButton(
        lastSVG,
        () => {
          currentPage = totalPages;
          resetSelection();
          fetchHistory();
        },
        page === totalPages,
      ),
    );
  }

  function filterLabelHandler() {
    document.querySelectorAll(".filter-option").forEach((btn) => {
      btn.addEventListener("click", () => {
        // reset active
        document
          .querySelectorAll(".filter-option")
          .forEach((b) => b.classList.remove("active"));

        // set active
        btn.classList.add("active");

        // set label
        const label = btn.dataset.label; // ambil dari data-attribute
        currentLabel = label || "";

        currentPage = 1;
        resetSelection();
        fetchHistory();
      });
    });
  }

  function sortingAccuracy() {
    const sortingAcc = document.querySelector(".sorting-accuracy");

    sortingAcc.onclick = () => {
      resetSortingUI("accuracy");

      // toggle order khusus accuracy
      accuracyOrder = accuracyOrder === "desc" ? "asc" : "desc";

      currentSortBy = "accuracy";
      currentOrder = accuracyOrder;

      // update icon
      document
        .querySelector(".accuracy-icon.default")
        ?.classList.toggle("active", accuracyOrder === "desc");

      document
        .querySelector(".accuracy-icon.sorted")
        ?.classList.toggle("active", accuracyOrder === "asc");

      sortingAcc.classList.add("active");

      currentPage = 1;
      resetSelection();
      fetchHistory();
    };
  }

  function sortingTime() {
    const select = document.getElementById("sorting-time");

    const optionTime = [
      { text: "Terbaru", value: "desc" },
      { text: "Terlama", value: "asc" },
    ];

    select.innerHTML = "";

    optionTime.forEach((opt) => {
      const option = document.createElement("option");
      option.value = opt.value;
      option.text = opt.text;
      select.appendChild(option);
    });

    select.onchange = function () {
      // reset sorting lain
      resetSortingUI("time");

      currentSortBy = "dibuat_pada"; // sesuai nama kolom di API
      currentOrder = this.value;

      resetSelection();
      fetchHistory();
    };
  }

  function resetSortingUI(except = "") {
    if (except !== "accuracy") {
      document.querySelector(".sorting-accuracy")?.classList.remove("active");

      document
        .querySelector(".accuracy-icon.sorted")
        ?.classList.remove("active");

      document.querySelector(".accuracy-icon.default")?.classList.add("active");
    }

    if (except !== "time") {
      const select = document.getElementById("sorting-time");

      if (select) {
        select.value = timeOrder;
      }
    }
  }

  // INIT
  fetchHistory();
  filterLabelHandler();
  sortingAccuracy();
  checkboxGlobalHandler();
  selectAllHandler();
  deleteSelectedHandler();
  sortingTime();
});
