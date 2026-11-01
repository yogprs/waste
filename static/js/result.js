document.addEventListener("DOMContentLoaded", () => {
  const session = sessionStorage.getItem("result-scan");
  const dataResult = session ? JSON.parse(session) : null;

  function setElementData() {
    if (!dataResult) return;

    const organicElement = document.querySelectorAll(".waste-type.organic");
    const nonOrganicElement = document.querySelectorAll(
      ".waste-type.non-organic",
    );

    const wasteImage = document.getElementById("waste-image");
    const typeText = document.getElementById("type-waste-text");
    const accuracyText = document.getElementById("accuracy");
    const instructionText = document.getElementById("waste-instruction");

    if (instructionText) instructionText.style.display = "block";

    const labelUpper = (dataResult.label || "").toUpperCase();

    if (labelUpper.includes("ORGANIK") && !labelUpper.includes("NON")) {
      if (organicElement[0]) organicElement[0].style.display = "inline-flex";
      if (nonOrganicElement[0]) nonOrganicElement[0].style.display = "none";
      if (instructionText) {
        instructionText.textContent =
          "Sampah ini termasuk organik, yaitu bahan yang mudah terurai secara alami yang dapat dimanfaatkan kembali menjadi kompos atau pupuk alami yang berguna untuk menyuburkan tanaman. \nDengan mengolah sampah organik, kamu membantu mengurangi limbah dan menjaga lingkungan tetap sehat.";
      }
    } else if (labelUpper.includes("NON") || labelUpper.includes("ANORGANIK")) {
      if (organicElement[0]) organicElement[0].style.display = "none";
      if (nonOrganicElement[0]) nonOrganicElement[0].style.display = "inline-flex";
      if (instructionText) {
        instructionText.textContent =
          "Sampah ini termasuk non-organik, yaitu bahan yang sulit terurai secara alami. Sampah jenis ini sebaiknya didaur ulang atau digunakan kembali agar tidak mencemari lingkungan. \nPisahkan sampah non-organik dengan benar agar dapat diproses menjadi produk baru yang bermanfaat.";
      }
    }

    if (wasteImage) {
      wasteImage.src = dataResult.image_url || dataResult.image || "";
    }
    if (typeText) {
      typeText.textContent = dataResult.label || "-";
    }
    if (accuracyText) {
      accuracyText.textContent = dataResult.accuracy || "-";
    }
  }

  function buttonNewScanTrigger() {
    const newScanButton = document.getElementById("new-scan");
    if (!newScanButton) return;

    newScanButton.addEventListener("click", () => {
      if (dataResult && dataResult.type === "stream") {
        window.location.href = "/detection/live";
      } else {
        window.location.href = "/detection";
      }
    });
  }

  function buttonHistoryTrigger() {
    const historyButton = document.getElementById("history");
    if (!historyButton) return;

    historyButton.addEventListener("click", () => {
      window.location.href = "/history";
    });
  }

  setElementData();
  buttonNewScanTrigger();
  buttonHistoryTrigger();
});
