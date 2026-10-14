/**
 * Intermediário do DataJud para a página index.html (a API pública do CNJ não libera CORS para navegadores).
 *
 * Publicar (uma vez, na conta Google do escritório):
 *  1. https://script.google.com > Novo projeto > colar este arquivo inteiro.
 *  2. Implantar > Nova implantação > tipo "App da Web" > Executar como: "Eu" > Quem pode acessar: "Qualquer pessoa".
 *  3. Copiar a URL (termina em /exec) e colar em DATAJUD_PROXY no index.html.
 *
 * Só consulta o DataJud por número de processo (20 dígitos, qualquer TJ, TRF, TRT, TRE ou STJ); não guarda nada.
 * Atualizar sem trocar a URL: Implantar > Gerenciar implantações > lápis > Versão: "Nova versão" > Implantar.
 * Fonte: API pública do DataJud (CNJ); a chave abaixo é a chave pública publicada na wiki do DataJud.
 */
var DATAJUD_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==";

function doGet(e) {
  var numero = String((e && e.parameter && e.parameter.numero) || "").replace(/\D/g, "");
  if (numero.length !== 20) return json_({ erro: "informe o número CNJ completo (20 dígitos)" });
  var alias = alias_(numero.charAt(13), numero.substr(14, 2));
  if (!alias) return json_({ erro: "tribunal deste número não está no DataJud público (segmento " + numero.charAt(13) + "." + numero.substr(14, 2) + ")" });
  var url = "https://api-publica.datajud.cnj.jus.br/api_publica_" + alias + "/_search";
  var corpo = JSON.stringify({ size: 10, query: { match: { numeroProcesso: numero } } });
  for (var t = 0; t < 4; t++) {  // o DataJud devolve 429/504 em horário de pico
    var r = UrlFetchApp.fetch(url, {
      method: "post", contentType: "application/json", payload: corpo, muteHttpExceptions: true,
      headers: { Authorization: "APIKey " + DATAJUD_KEY }
    });
    if (r.getResponseCode() === 200) {
      return json_({ tribunal: alias, hits: JSON.parse(r.getContentText()).hits.hits });
    }
    Utilities.sleep(3000 * (t + 1));
  }
  return json_({ erro: "DataJud ocupado; tente de novo em alguns minutos" });
}

// Dígito J (segmento) + TR do número CNJ (Res. CNJ 65/2008) -> alias da API pública do DataJud
function alias_(j, tr) {
  var UF = ["", "ac", "al", "ap", "am", "ba", "ce", "dft", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb", "pr", "pe",
            "pi", "rj", "rn", "rs", "ro", "rr", "sc", "se", "sp", "to"];
  var n = parseInt(tr, 10);
  if (j === "8" && UF[n]) return "tj" + UF[n];
  if (j === "4" && n >= 1 && n <= 6) return "trf" + n;
  if (j === "5" && n >= 1 && n <= 24) return "trt" + n;
  if (j === "6" && UF[n]) return "tre-" + UF[n];
  if (j === "3") return "stj";
  return null;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
