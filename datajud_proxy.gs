/**
 * Intermediário do DataJud para a página index.html (a API pública do CNJ não libera CORS para navegadores).
 *
 * Publicar (uma vez, na conta Google do escritório):
 *  1. https://script.google.com > Novo projeto > colar este arquivo inteiro.
 *  2. Implantar > Nova implantação > tipo "App da Web" > Executar como: "Eu" > Quem pode acessar: "Qualquer pessoa".
 *  3. Copiar a URL (termina em /exec) e colar em DATAJUD_PROXY no index.html.
 *
 * Só consulta o DataJud do TJAM por número de processo (20 dígitos); não guarda nada.
 * Fonte: API pública do DataJud (CNJ); a chave abaixo é a chave pública publicada na wiki do DataJud.
 */
var DATAJUD_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==";

function doGet(e) {
  var numero = String((e && e.parameter && e.parameter.numero) || "").replace(/\D/g, "");
  if (numero.length !== 20 || numero.substr(13, 3) !== "804") {
    return json_({ erro: "informe um número CNJ do TJAM (20 dígitos, segmento 8.04)" });
  }
  var url = "https://api-publica.datajud.cnj.jus.br/api_publica_tjam/_search";
  var corpo = JSON.stringify({ size: 10, query: { match: { numeroProcesso: numero } } });
  for (var t = 0; t < 4; t++) {  // o DataJud devolve 429/504 em horário de pico
    var r = UrlFetchApp.fetch(url, {
      method: "post", contentType: "application/json", payload: corpo, muteHttpExceptions: true,
      headers: { Authorization: "APIKey " + DATAJUD_KEY }
    });
    if (r.getResponseCode() === 200) {
      return json_({ hits: JSON.parse(r.getContentText()).hits.hits });
    }
    Utilities.sleep(3000 * (t + 1));
  }
  return json_({ erro: "DataJud ocupado; tente de novo em alguns minutos" });
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
