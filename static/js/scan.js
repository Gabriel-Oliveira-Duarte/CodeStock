const statusScanner = document.getElementById("statusScanner");
const btnIniciarScanner = document.getElementById("btnIniciarScanner");
const btnPararScanner = document.getElementById("btnPararScanner");
const formBuscaManual = document.getElementById("formBuscaManual");
const codigoManual = document.getElementById("codigoManual");

let scanner = null;
let scannerAtivo = false;
let leituraProcessada = false;

function setStatus(message, type = "info") {
  if (!statusScanner) return;
  statusScanner.textContent = message;
  statusScanner.classList.remove("success", "error");

  if (type === "success") statusScanner.classList.add("success");
  if (type === "error") statusScanner.classList.add("error");
}

function normalizarCodigo(valor) {
  return (valor || "").trim().replace(/^\/+|\/+$/g, "");
}

function montarUrlMaterial(codigo) {
  const base = window.CODESTOCK_SCAN?.materialBaseUrl || "/material/__CODIGO__";
  return base.replace("__CODIGO__", encodeURIComponent(codigo));
}

function extrairCodigoDoQr(texto) {
  const conteudo = (texto || "").trim();

  if (!conteudo) return "";

  try {
    const url = new URL(conteudo);
    const partes = url.pathname.split("/").filter(Boolean);
    const indiceMaterial = partes.findIndex((parte) => parte.toLowerCase() === "material");

    if (indiceMaterial >= 0 && partes[indiceMaterial + 1]) {
      return decodeURIComponent(partes[indiceMaterial + 1]);
    }
  } catch (error) {
    // Não era uma URL completa. Continua tentando como texto comum.
  }

  if (conteudo.includes("/material/")) {
    const partes = conteudo.split("/material/");
    return decodeURIComponent((partes[1] || "").split(/[?#]/)[0]);
  }

  return normalizarCodigo(conteudo);
}

function abrirMaterialPorCodigo(codigo) {
  const codigoLimpo = normalizarCodigo(codigo);

  if (!codigoLimpo) {
    setStatus("Código inválido. Tente novamente ou use a busca manual.", "error");
    leituraProcessada = false;
    return;
  }

  setStatus(`Material ${codigoLimpo} identificado. Abrindo ficha...`, "success");
  window.location.href = montarUrlMaterial(codigoLimpo);
}

function onScanSuccess(decodedText) {
  if (leituraProcessada) return;

  leituraProcessada = true;
  const codigo = extrairCodigoDoQr(decodedText);
  abrirMaterialPorCodigo(codigo);
}

function onScanFailure() {
  // A biblioteca chama esta função várias vezes enquanto procura o QR.
  // Não exibimos erro contínuo para não poluir a tela.
}

async function iniciarScanner() {
  if (scannerAtivo) return;

  if (!window.Html5Qrcode) {
    setStatus("Biblioteca de leitura QR não carregada. Verifique a conexão com a internet.", "error");
    return;
  }

  try {
    scanner = new Html5Qrcode("reader");
    leituraProcessada = false;

    await scanner.start(
      { facingMode: "environment" },
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0
      },
      onScanSuccess,
      onScanFailure
    );

    scannerAtivo = true;
    setStatus("Scanner ativo. Posicione o QR Code dentro da área marcada.");
  } catch (error) {
    console.error(error);
    setStatus("Não foi possível acessar a câmera. Use HTTPS/ngrok ou tente a busca manual.", "error");
  }
}

async function pararScanner() {
  if (!scanner || !scannerAtivo) {
    setStatus("Scanner já está parado.");
    return;
  }

  try {
    await scanner.stop();
    await scanner.clear();
    scannerAtivo = false;
    leituraProcessada = false;
    setStatus("Scanner parado. Clique em iniciar para ler novamente.");
  } catch (error) {
    console.error(error);
    setStatus("Não foi possível parar o scanner agora.", "error");
  }
}

btnIniciarScanner?.addEventListener("click", iniciarScanner);
btnPararScanner?.addEventListener("click", pararScanner);

formBuscaManual?.addEventListener("submit", function (event) {
  event.preventDefault();
  abrirMaterialPorCodigo(codigoManual?.value || "");
});

document.addEventListener("DOMContentLoaded", function () {
  setStatus("Clique em iniciar scanner e permita o acesso à câmera.");

  // Em celular, iniciar automaticamente costuma deixar a experiência mais fluida.
  // Se o navegador bloquear, o botão manual continua disponível.
  if (window.innerWidth <= 900) {
    setTimeout(iniciarScanner, 700);
  }
});
