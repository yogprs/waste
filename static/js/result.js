document.addEventListener("DOMContentLoaded", () => {
  const session = sessionStorage.getItem("result-scan");
  const dataResult = JSON.parse(session);

  function setELementData() {
    const organicElement = document.querySelectorAll(".waste-type.organic");
    const nonOrganicElement = document.querySelectorAll(
      ".waste-type.non-organic",
    );

    const wasteImage = document.getElementById("waste-image");
    const typeText = document.getElementById("type-waste-text");
    const accuracyText = document.getElementById("accuracy");
    const instructionText = document.getElementById("waste-instruction");

    instructionText.style.display = "block";
    if (dataResult.label === "Organik") {
      organicElement[0].style.display = "inline-flex";
      nonOrganicElement[0].style.display = "none";
      instructionText.textContent =
        "Sampah ini termasuk organik, yaitu bahan yang mudah terurai secara alami yang dapat dimanfaatkan kembali menjadi kompos atau pupuk alami yang berguna untuk menyuburkan tanaman. \nDengan mengolah sampah organik, kamu membantu mengurangi limbah dan menjaga lingkungan tetap sehat.";
    } else if (dataResult.label === "Non-Organik") {
      organicElement[0].style.display = "none";
      nonOrganicElement[0].style.display = "inline-flex";
      instructionText.textContent =
        "Sampah ini termasuk non-organik, yaitu bahan yang sulit terurai secara alami. Sampah jenis ini sebaiknya didaur ulang atau digunakan kembali agar tidak mencemari lingkungan. \nPisahkan sampah non-organik dengan benar agar dapat diproses menjadi produk baru yang bermanfaat.";
    }

    wasteImage.src = dataResult.image_url;
    typeText.textContent = dataResult.label;
    accuracyText.textContent = dataResult.accuracy;
  }

  function buttonNewScanTrigger() {
    const newScanButton = document.getElementById("new-scan");

    newScanButton.addEventListener("click", () => {
      if (dataResult.type === "upload") {
        window.location.href = "/detection";
      } else if (dataResult.type === "stream") {
        window.location.href = "/detection/live";
      }
    });
  }

  function buttonHistoryTrigger() {
    const historyButton = document.getElementById("history");

    historyButton.addEventListener("click", () => {
      window.location.href = "/history";
    });
  }
  setELementData();
  buttonNewScanTrigger();
  buttonHistoryTrigger();
});
