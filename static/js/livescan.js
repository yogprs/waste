document.addEventListener("DOMContentLoaded", () => {
  let currentStream = null;
  let frameInterval = null;
  let isStreamingProcessing = false;
  let isManualCapturing = false;
  let hasRedirected = false;

  function stopCameraStream() {
    if (currentStream) {
      currentStream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch (e) {
          console.warn("Error stopping track:", e);
        }
      });
      currentStream = null;
    }
  }

  // Bersihkan kamera saat meninggalkan halaman
  window.addEventListener("beforeunload", () => {
    stopCameraStream();
    if (frameInterval) clearInterval(frameInterval);
  });

  async function getCameras() {
    const select = document.getElementById("cameraSelect");
    const detectionStatus = document.getElementById("detection-status");

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (detectionStatus) {
          detectionStatus.innerText = "KAMERA TIDAK DIDUKUNG";
          detectionStatus.style.backgroundColor = "rgba(220, 53, 69, 0.85)";
        }
        return;
      }

      // Minta izin akses kamera
      const initStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });

      // Dapatkan daftar perangkat kamera
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cameras = devices.filter((device) => device.kind === "videoinput");

      if (select) {
        select.innerHTML = "";
        cameras.forEach((camera, index) => {
          const option = document.createElement("option");
          option.value = camera.deviceId;
          option.text = camera.label || `Kamera ${index + 1}`;
          select.appendChild(option);
        });
      }

      // Langsung nyalakan kamera pertama
      if (cameras.length > 0) {
        await startCamera(cameras[0].deviceId);
      } else {
        const video = document.getElementById("video");
        if (video) video.srcObject = initStream;
        currentStream = initStream;
      }
    } catch (err) {
      console.error("Gagal mendapatkan akses kamera:", err);
      if (detectionStatus) {
        detectionStatus.innerText = "IZIN KAMERA DITOLAK ATAU TIDAK ADA";
        detectionStatus.style.backgroundColor = "rgba(220, 53, 69, 0.85)";
      }
    }
  }

  async function startCamera(deviceId) {
    stopCameraStream();

    const video = document.getElementById("video");
    const detectionStatus = document.getElementById("detection-status");

    try {
      const constraints = {
        audio: false,
        video: deviceId
          ? { deviceId: { ideal: deviceId }, width: { ideal: 1280 }, height: { ideal: 720 } }
          : { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } },
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      if (video) {
        video.srcObject = stream;
        await video.play().catch(() => {});
      }
      currentStream = stream;
    } catch (err) {
      console.warn("Gagal membuka kamera dengan constraint spesifik, coba fallback:", err);
      try {
        const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        if (video) {
          video.srcObject = fallbackStream;
          await video.play().catch(() => {});
        }
        currentStream = fallbackStream;
      } catch (fallbackErr) {
        console.error("Fallback kamera juga gagal:", fallbackErr);
        if (detectionStatus) {
          detectionStatus.innerText = "GAGAL MEMBUKA KAMERA";
          detectionStatus.style.backgroundColor = "rgba(220, 53, 69, 0.85)";
        }
      }
    }
  }

  const cameraSelect = document.getElementById("cameraSelect");
  if (cameraSelect) {
    cameraSelect.onchange = function () {
      if (this.value) {
        startCamera(this.value);
      }
    };
  }

  function backButtonHandler() {
    const backButton = document.getElementById("back-button");
    if (!backButton) return;

    backButton.addEventListener("click", () => {
      stopCameraStream();
      if (frameInterval) clearInterval(frameInterval);

      if (document.referrer && !document.referrer.includes("/login")) {
        window.history.back();
      } else {
        window.location.href = "/detection";
      }
    });
  }

  function socketVideo() {
    const video = document.getElementById("video");
    const detectionBox = document.getElementById("detection-box");
    const detectionStatus = document.getElementById("detection-status");
    const resultImg = document.getElementById("resultImage");

    if (!video) return;

    // Inisialisasi Socket.IO
    const socket = typeof io === "function" ? io() : null;

    if (!socket) {
      console.warn("Socket.io tidak tersedia.");
      return;
    }

    socket.on("connect", () => {
      console.log("Socket terhubung dengan SID:", socket.id);
    });

    socket.on("response_back", (msg) => {
      isStreamingProcessing = false;

      if (hasRedirected) return;

      if (resultImg && msg?.image) {
        resultImg.src = msg.image;
      }

      // Jika ada error dari server
      if (msg?.error) {
        console.warn("Deteksi error:", msg.error);
        if (detectionStatus) {
          detectionStatus.innerText = msg.error;
          detectionStatus.style.backgroundColor = "rgba(220, 53, 69, 0.85)";
        }
        if (msg.error.toLowerCase().includes("tidak ditemukan") || msg.error.toLowerCase().includes("login")) {
          alert(msg.error);
          localStorage.clear();
          sessionStorage.clear();
          window.location.href = "/login";
        }
        return;
      }

      // Jika belum ada sampah yang terdeteksi
      if (!msg?.label) {
        if (detectionBox) {
          detectionBox.style.borderColor = "#ffffff";
        }
        if (detectionStatus) {
          detectionStatus.innerText = "MENCARI SAMPAH...";
          detectionStatus.style.backgroundColor = "rgba(15, 82, 56, 0.85)";
        }
        return;
      }

      // Visual feedback: sampah terdeteksi!
      if (detectionBox) {
        detectionBox.style.borderColor = "#28a745";
      }

      // Cek apakah upload dan simpan riwayat di database sudah selesai (image_url sudah ada)
      if (msg.image_url) {
        hasRedirected = true;
        if (frameInterval) clearInterval(frameInterval);

        if (detectionStatus) {
          detectionStatus.innerText = `TERDETEKSI: ${msg.label} (${msg.accuracy || ""}) - MEMBUKA HASIL...`;
          detectionStatus.style.backgroundColor = "rgba(40, 167, 69, 0.95)";
        }

        sessionStorage.setItem(
          "result-scan",
          JSON.stringify({
            image: msg.image_url || msg.image,
            label: msg.label,
            label_with_accuracy: msg.label_with_accuracy || `${msg.label} (${msg.accuracy || ""})`,
            accuracy: msg.accuracy || "",
            image_url: msg.image_url,
            type: msg.type || "stream",
          }),
        );

        stopCameraStream();
        video.style.opacity = "0.5";

        setTimeout(() => {
          window.location.href = "/detection/result";
        }, 300);
      } else {
        // Label terdeteksi, server sedang mengunggah gambar dan menyimpan riwayat
        if (detectionStatus) {
          detectionStatus.innerText = `SAMPAH TERDETEKSI: ${msg.label_with_accuracy || msg.label}! MENYIMPAN...`;
          detectionStatus.style.backgroundColor = "rgba(40, 167, 69, 0.85)";
        }
      }
    });

    function sendFrame() {
      if (isStreamingProcessing || isManualCapturing || hasRedirected) return;
      if (!video || video.videoWidth === 0 || video.videoHeight === 0) return;

      const storageLocal = localStorage.getItem("user");
      const dataUser = storageLocal ? JSON.parse(storageLocal) : null;
      if (!dataUser || !dataUser.id) return;

      const userRole = (dataUser.role || dataUser.user_type || "").toLowerCase();
      if (!userRole) return;

      isStreamingProcessing = true;

      let width = video.videoWidth;
      let height = video.videoHeight;

      // Resize maksimal 640px untuk efisiensi stream realtime
      if (width > 640) {
        const ratio = 640 / width;
        width = 640;
        height = height * ratio;
      }

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, width, height);

      const data = canvas.toDataURL("image/jpeg", 0.7);
      if (!data || data.length < 100) {
        isStreamingProcessing = false;
        return;
      }

      socket.emit("image", {
        image: data,
        user_id: dataUser.id,
        user_type: userRole,
      });
    }

    frameInterval = setInterval(sendFrame, 400);
  }

  function manualScanButton() {
    const video = document.getElementById("video");
    const scanNowBtn = document.getElementById("scan-now-btn");
    const detectionStatus = document.getElementById("detection-status");
    const detectionBox = document.getElementById("detection-box");

    if (!scanNowBtn) return;

    function resetScanButton() {
      isManualCapturing = false;
      scanNowBtn.disabled = false;
      scanNowBtn.classList.remove("scanning");
      scanNowBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
          <path fill="currentColor" d="M12 17q1.875 0 3.188-1.312T16.5 12.5q0-1.875-1.312-3.187T12 8q-1.875 0-3.187 1.313T7.5 12.5q0 1.875 1.313 3.188T12 17m0-2q-1.05 0-1.775-.725T9.5 12.5q0-1.05.725-1.775T12 10t1.775.725T14.5 12.5t-.725 1.775T12 15M4 21q-.825 0-1.412-.587T2 19V8q0-.825.588-1.412T4 6h3l2-2h6l2 2h3q.825 0 1.413.588T22 8v11q0 .825-.587 1.413T20 21z"/>
        </svg>
        Scan Sekarang`;
    }

    scanNowBtn.addEventListener("click", async () => {
      if (isManualCapturing || hasRedirected) return;
      if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
        alert("Kamera belum siap, tunggu beberapa detik lalu coba lagi.");
        return;
      }

      const storageLocal = localStorage.getItem("user");
      const dataUser = storageLocal ? JSON.parse(storageLocal) : null;
      const userId = dataUser?.id;
      const userRole = (dataUser?.role || dataUser?.user_type || "").toLowerCase();

      if (!userId || !userRole) {
        alert("Sesi login tidak ditemukan, silakan login kembali.");
        window.location.href = "/login";
        return;
      }

      isManualCapturing = true;
      scanNowBtn.disabled = true;
      scanNowBtn.classList.add("scanning");
      scanNowBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">
          <path fill="currentColor" d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2m0 18a8 8 0 1 1 8-8a8 8 0 0 1-8 8"/>
          <path fill="currentColor" d="M20 12h2A10 10 0 0 0 12 2v2a8 8 0 0 1 8 8" opacity="0.5">
            <animateTransform attributeName="transform" dur="1s" from="0 12 12" repeatCount="indefinite" to="360 12 12" type="rotate"/>
          </path>
        </svg>
        Memindai...`;

      if (detectionStatus) {
        detectionStatus.innerText = "SEDANG MEMINDAI...";
        detectionStatus.style.backgroundColor = "rgba(15, 82, 56, 0.85)";
      }

      try {
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise((resolve) =>
          canvas.toBlob(resolve, "image/jpeg", 0.9),
        );

        if (!blob) {
          resetScanButton();
          return;
        }

        const formData = new FormData();
        formData.append("file", blob, "scan_capture.jpg");
        formData.append("center_roi", "true");
        formData.append("role", userRole);

        const response = await fetch(`/api/upload/${userId}`, {
          method: "POST",
          body: formData,
        });

        const result = await response.json();

        if (!response.ok || result.error || !result.label) {
          const errMsg = result.error || "Item tidak terdeteksi, silakan coba lagi.";
          if (errMsg.toLowerCase().includes("tidak ditemukan") || errMsg.toLowerCase().includes("login")) {
            alert(errMsg);
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = "/login";
            return;
          }
          if (detectionStatus) {
            detectionStatus.innerText = errMsg.toUpperCase();
            detectionStatus.style.backgroundColor = "rgba(220, 53, 69, 0.85)";
            setTimeout(() => {
              detectionStatus.innerText = "MENCARI SAMPAH...";
              detectionStatus.style.backgroundColor = "rgba(15, 82, 56, 0.85)";
            }, 3000);
          }
          if (detectionBox) {
            detectionBox.style.borderColor = "#dc3545";
            setTimeout(() => {
              detectionBox.style.borderColor = "#ffffff";
            }, 3000);
          }
          resetScanButton();
          return;
        }

        // Berhasil terdeteksi!
        hasRedirected = true;
        if (frameInterval) clearInterval(frameInterval);

        if (detectionBox) detectionBox.style.borderColor = "#28a745";
        if (detectionStatus) {
          detectionStatus.innerText = `TERDETEKSI: ${result.label} (${result.accuracy || ""}) - MEMBUKA HASIL...`;
          detectionStatus.style.backgroundColor = "rgba(40, 167, 69, 0.95)";
        }

        sessionStorage.setItem(
          "result-scan",
          JSON.stringify({
            image: result.image_url,
            label: result.label,
            label_with_accuracy: result.label_with_accuracy || `${result.label} (${result.accuracy || ""})`,
            accuracy: result.accuracy || "",
            image_url: result.image_url,
            type: result.type || "upload",
          }),
        );

        stopCameraStream();
        video.style.opacity = "0.5";

        setTimeout(() => {
          window.location.href = "/detection/result";
        }, 300);
      } catch (err) {
        console.error("Gagal melakukan scan manual:", err);
        if (detectionStatus) {
          detectionStatus.innerText = "TERJADI KESALAHAN KONEKSI";
          detectionStatus.style.backgroundColor = "rgba(220, 53, 69, 0.85)";
          setTimeout(() => {
            detectionStatus.innerText = "MENCARI SAMPAH...";
            detectionStatus.style.backgroundColor = "rgba(15, 82, 56, 0.85)";
          }, 3000);
        }
        resetScanButton();
      }
    });
  }

  // Jalankan modul
  getCameras();
  backButtonHandler();
  socketVideo();
  manualScanButton();
});
