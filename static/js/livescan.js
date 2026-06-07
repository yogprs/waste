document.addEventListener("DOMContentLoaded", () => {
  let currentStream;

  async function getCameras() {
    // 🚨 WAJIB: trigger permission dulu
    await navigator.mediaDevices.getUserMedia({ video: true });

    const devices = await navigator.mediaDevices.enumerateDevices();
    const cameras = devices.filter((device) => device.kind === "videoinput");

    const select = document.getElementById("cameraSelect");
    select.innerHTML = "";

    cameras.forEach((camera, index) => {
      const option = document.createElement("option");
      option.value = camera.deviceId;
      option.text = camera.label || `Camera ${index + 1}`;

      select.appendChild(option);
    });

    // 🚀 langsung nyalakan kamera pertama
    if (cameras.length > 0) {
      startCamera(cameras[0].deviceId);
    }
  }

  async function startCamera(deviceId) {
    if (currentStream) {
      currentStream.getTracks().forEach((track) => track.stop());
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      video: { deviceId: { exact: deviceId } },
    });

    // const stream = await navigator.mediaDevices.getUserMedia({
    //   video: true,
    // });

    document.getElementById("video").srcObject = stream;
    currentStream = stream;
  }

  document.getElementById("cameraSelect").onchange = function () {
    startCamera(this.value);
  };

  function backButtonHandler() {
    const backButton = document.getElementById("back-button");

    backButton.addEventListener("click", () => {
      if (document.referrer) {
        window.history.back();
      } else {
        window.location.href = "/detection";
      }
    });
  }

  function socketVideo() {
    const video = document.getElementById("video");
    const socket = io();

    let isProcessing = false;

    socket.on("connect", () => {
      console.log("Socket terhubung!");
    });

    function redirectToResult() {
      window.location.href = "/detection/result";
    }

    socket.on("response_back", function (msg) {
      isProcessing = false;

      const resultImg = document.getElementById("resultImage");
      resultImg.src = msg.image;

      if (!msg.label) return;

      sessionStorage.setItem(
        "result-scan",
        JSON.stringify({
          image: msg.image,
          label: msg.label,
          label_with_accuracy: msg.label_with_accuracy,
          accuracy: msg.accuracy,
          image_url: msg.image_url,
          type: msg.type,
        }),
      );

      redirectToResult();
      // setTimeout(redirectToResult, 500);
    });
    const storageLocal = localStorage.getItem("user");
    const dataUser = JSON.parse(storageLocal);
    function sendFrame() {
      if (isProcessing) return;

      if (video.videoWidth === 0 || video.videoHeight === 0) {
        return;
      }

      isProcessing = true;

      let width = video.videoWidth;
      let height = video.videoHeight;

      // Resize set maksimal 640px untuk performance streaming realtime
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

      const data = canvas.toDataURL("image/jpeg", 0.7); // compress JPEG

      if (!data || data.length < 100) return;

      socket.emit("image", { image: data, user_id: dataUser.id });
    }

    video.onloadedmetadata = () => {
      console.log("Video ready, mulai stream..");
      // Kirim 10 frames per second (500ms) untuk real-time experience

      // 6 (166ms), 12 (83ms), 24 (41ms) fps
      setInterval(sendFrame, 800);
      // setInterval(sendFrame, 600);
    };
  }

  getCameras();
  backButtonHandler();
  socketVideo();
});
