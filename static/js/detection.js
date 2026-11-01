const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-file-btn");

// Klik "browse files" buka file picker
browseBtn.addEventListener("click", () => fileInput.click());

// cegah default behavior (biar tidak buka file di browser)
["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
});

// efek saat drag masuk
["dragenter", "dragover"].forEach((eventName) => {
  dropArea.addEventListener(eventName, () => {
    dropArea.classList.add("dragging");
  });
});

// hapus efek saat keluar
["dragleave", "drop"].forEach((eventName) => {
  dropArea.addEventListener(eventName, () => {
    dropArea.classList.remove("dragging");
  });
});

// handle file drop
dropArea.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;

  if (files.length > 0) {
    uploadFile(files[0]);
  }
});

// File selected via browse
fileInput.addEventListener("change", () => {
  handleFiles(fileInput.files);
});

function redirectToResult() {
  window.location.href = "/detection/result";
}

function sendImageToAPI(file) {
  const storageLocal = localStorage.getItem("user");
  const dataUser = JSON.parse(storageLocal);

  if (!dataUser.id) return;

  if (!file.type.startsWith("image/")) {
    alert("Please upload an image file!");
    return;
  }

  // Validasi ukuran file (maks 20MB)
  const maxSize = 20 * 1024 * 1024; // 20MB dalam bytes
  if (file.size > maxSize) {
    alert("Ukuran file tidak boleh lebih dari 20MB!");
    return;
  }

  // Kirim file ke Flask via fetch
  const formData = new FormData();
  formData.append("file", file);
  formData.append("role", dataUser.role); // wajib dikirim ke API

  fetch(`/api/upload/${dataUser.id}`, {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }
      sessionStorage.setItem(
        "result-scan",
        JSON.stringify({
          image: data.image,
          label: data.label,
          label_with_accuracy: data.label_with_accuracy,
          image_url: data.image_url,
          accuracy: data.accuracy,
          type: data.type,
        }),
      );

      redirectToResult();
      // setInterval(redirectToResult, 500);
    })
    .catch((err) => {
      console.error("Error:", err);
    });
}

// fungsi upload
function uploadFile(file) {
  console.log("File diterima:", file);

  sendImageToAPI(file);
}

// Process files
function handleFiles(files) {
  if (files.length === 0) return;
  const file = files[0];

  sendImageToAPI(file);
}

const cameraButton = document.getElementById("camera-button");

cameraButton.addEventListener("click", () => {
  window.location.href = "/detection/live";
});
