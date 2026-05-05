const statusScanner = document.getElementById("statusScanner");

function onScanSuccess(decodedText) {
  statusScanner.textContent = "QR Code lido. Redirecionando...";

  // 🔥 redireciona direto
  window.location.href = decodedText;
}

function onScanFailure(error) {
  // ignora erros contínuos da câmera
}

const scanner = new Html5Qrcode("reader");

scanner.start(
  { facingMode: "environment" },
  {
    fps: 10,
    qrbox: {
      width: 250,
      height: 250
    }
  },
  onScanSuccess,
  onScanFailure
).catch((err) => {
  statusScanner.textContent = "Erro ao acessar câmera.";
  console.error(err);
});