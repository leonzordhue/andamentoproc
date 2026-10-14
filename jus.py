"""Consultas jurídicas públicas para os projetos do Paulo (LAADV e afins).

Três comandos (saída em ./saida, NÃO compartilhar: pode conter nomes de partes e advogados):

  python jus.py jurisprudencia "progressão funcional servidor" [--tribunal TJAM] [--paginas 2]
      Acórdãos do tribunal (e-SAJ/portal do tribunal, via juscraper): processo, órgão, relator, datas, ementa.
      Tribunais: TJAM e mais 26 TJs, STF, TRF1/3/5/6 (os mesmos módulos do juscraper).

  python jus.py processo 0620084-16.2022.8.04.0001 [outro ...]
      Metadados e movimentos de cada processo pela API pública do CNJ (DataJud). Guarda um retrato em
      saida/processos/<numero>.json e mostra só os movimentos NOVOS desde a última consulta (monitoramento).
      O DataJud não traz partes nem documentos.

  python jus.py intimacoes "NOME DO ADVOGADO ou OAB 1234" [--desde 2026-10-01] [--tribunal todos]
      Comunicações/intimações publicadas no Diário de Justiça Eletrônico Nacional (Comunica PJe / CNJ).
      Padrão: só TJAM (todos os comandos partem do TJAM; o de processo deduz o tribunal pelo número).

Fontes: juscraper 0.4 (MIT, github.com/jtrecenti/juscraper); DataJud (CNJ, chave pública da wiki do DataJud);
Comunica PJe (comunica.pje.jus.br). Só dados públicos; respeitar o ritmo das APIs (há espera entre tentativas).
"""
import argparse
import json
import os
import re
import sys
import time

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE_DIR, "saida")
DATAJUD_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="  # chave pública do CNJ
# Segmento de justiça (dígito J do CNJ) + tribunal (TR) -> alias do DataJud; só o necessário no AM e superiores.
DATAJUD_ALIAS = {("8", "04"): "tjam", ("4", "01"): "trf1", ("5", "11"): "trt11", ("6", "04"): "tre-am"}


def _so_digitos(n):
    return re.sub(r"\D", "", n)


def alias_datajud(numero):
    d = _so_digitos(numero)
    if len(d) != 20:
        raise SystemExit("número CNJ inválido (precisa de 20 dígitos): %s" % numero)
    j, tr = d[13], d[14:16]
    if (j, tr) in DATAJUD_ALIAS:
        return DATAJUD_ALIAS[(j, tr)]
    if j == "8":
        return "tj" + {"01": "ac", "02": "al", "03": "ap", "05": "ba", "06": "ce", "07": "dft", "08": "es", "09": "go",
                       "10": "ma", "11": "mt", "12": "ms", "13": "mg", "14": "pa", "15": "pb", "16": "pr", "17": "pe",
                       "18": "pi", "19": "rj", "20": "rn", "21": "rs", "22": "ro", "23": "rr", "24": "sc", "25": "se",
                       "26": "sp", "27": "to"}[tr]
    if j == "3":
        return "stj"
    raise SystemExit("tribunal do número %s não mapeado; acrescente em DATAJUD_ALIAS" % numero)


def datajud(alias, consulta, tentativas=8):
    """POST na API pública do DataJud com novas tentativas: o servidor do CNJ devolve 429/504 em horário de pico."""
    url = "https://api-publica.datajud.cnj.jus.br/api_publica_%s/_search" % alias
    for t in range(tentativas):
        try:
            r = requests.post(url, json=consulta, headers={"Authorization": "APIKey " + DATAJUD_KEY}, timeout=90)
            if r.status_code == 200:
                return r.json()["hits"]["hits"]
            erro = r.status_code
        except requests.RequestException as e:
            erro = type(e).__name__
        espera = 10 + 5 * t
        print("  DataJud ocupado (%s); nova tentativa em %d s" % (erro, espera), file=sys.stderr)
        time.sleep(espera)
    raise SystemExit("DataJud indisponível agora; tente mais tarde")


def cmd_processo(a):
    pasta = os.path.join(SAIDA, "processos")
    os.makedirs(pasta, exist_ok=True)
    for numero in a.numeros:
        d = _so_digitos(numero)
        hits = datajud(alias_datajud(d), {"size": 10, "query": {"match": {"numeroProcesso": d}}})
        if not hits:
            # Processo novo demora semanas para entrar no DataJud: procura as publicações dele no DJEN.
            print("\n%s: não encontrado no DataJud (processo recente?); publicações no DJEN:" % numero)
            import juscraper
            fmt = "%s-%s.%s.%s.%s.%s" % (d[:7], d[7:9], d[9:13], d[13], d[14:16], d[16:])
            df = juscraper.scraper("comunica_cnj").listar_comunicacoes(fmt, paginas=1)
            df = df[df["numeroprocessocommascara"] == fmt] if len(df) else df
            for _, r in df.sort_values("data_disponibilizacao").iterrows():
                print("   %s %s | %s | %s" % (r["datadisponibilizacao"], r["tipoComunicacao"], r["nomeOrgao"], r.get("tipoDocumento")))
                print("     " + re.sub(r"<[^>]+>", " ", str(r["texto"]))[:400])
            if not len(df):
                print("   (nenhuma)")
            continue
        # O DataJud pode ter um registro por grau (G1, G2...): mostra todos.
        movs_atuais = set()
        print("\n" + "=" * 100)
        for h in hits:
            s = h["_source"]
            print("%s | %s | %s | %s | ajuizado %s | atualizado %s" % (
                s.get("numeroProcesso"), s.get("grau"), s.get("classe", {}).get("nome"),
                s.get("orgaoJulgador", {}).get("nome"), str(s.get("dataAjuizamento"))[:8],
                str(s.get("dataHoraUltimaAtualizacao"))[:10]))
            print("  assuntos:", "; ".join(x.get("nome", "") for x in s.get("assuntos", [])))
            for m in s.get("movimentos", []):
                movs_atuais.add("%s|%s|%s|%s" % (s.get("grau"), m.get("dataHora", "")[:19], m.get("codigo"), m.get("nome")))
        arq = os.path.join(pasta, d + ".json")
        antes = set(json.load(open(arq, encoding="utf-8"))) if os.path.exists(arq) else None
        por_data = lambda m: m.split("|")[1]
        novos = sorted(movs_atuais - antes, key=por_data) if antes is not None else sorted(movs_atuais, key=por_data)[-a.ultimos:]
        print("  %s:" % ("movimentos NOVOS desde a última consulta" if antes is not None else "últimos %d movimentos" % a.ultimos))
        for m in novos:
            g, dh, cod, nome = m.split("|", 3)
            print("   %s %s %s (%s)" % (dh[:10], g, nome, cod))
        if antes is not None and not novos:
            print("   (nenhum)")
        json.dump(sorted(movs_atuais), open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


def _salvar(df, nome):
    os.makedirs(SAIDA, exist_ok=True)
    arq = os.path.join(SAIDA, nome + ".xlsx")
    df.to_excel(arq, index=False)
    return arq


def cmd_jurisprudencia(a):
    import juscraper
    s = juscraper.scraper(a.tribunal.lower())
    df = s.cjsg(a.termos, paginas=a.paginas)
    print("%d acórdãos (%s, %d página(s))" % (len(df), a.tribunal.upper(), a.paginas))
    for _, r in df.head(a.mostrar).iterrows():
        print("\n- %s | %s | %s | julgado %s" % (r.get("processo"), r.get("orgao_julgador"), r.get("relatora") or r.get("relator"),
                                              r.get("data_julgamento")))
        print("  " + str(r.get("ementa") or "")[:400].replace("\n", " "))
    if len(df):
        nome = "juris_%s_%s" % (a.tribunal.lower(), re.sub(r"\W+", "_", a.termos)[:40])
        print("\nplanilha completa:", _salvar(df, nome))


def cmd_intimacoes(a):
    import juscraper
    c = juscraper.scraper("comunica_cnj")
    kw = {"data_disponibilizacao_inicio": a.desde} if a.desde else {}
    df = c.listar_comunicacoes(a.termos, paginas=a.paginas, **kw)
    if len(df) and a.tribunal.lower() != "todos":  # padrão do Paulo: só TJAM
        df = df[df["siglaTribunal"].str.upper() == a.tribunal.upper()]
    print("%d comunicações (%s)" % (len(df), a.tribunal.upper()))
    for _, r in df.head(a.mostrar).iterrows():
        print("\n- %s | %s | %s | %s | %s" % (r.get("datadisponibilizacao"), r.get("siglaTribunal"), r.get("numeroprocessocommascara"),
                                           r.get("tipoComunicacao"), r.get("nomeOrgao")))
        print("  " + str(r.get("texto") or "")[:300].replace("\n", " "))
    if len(df):
        print("\nplanilha completa:", _salvar(df, "intimacoes_" + re.sub(r"\W+", "_", a.termos)[:40]))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    j = sub.add_parser("jurisprudencia")
    j.add_argument("termos")
    j.add_argument("--tribunal", default="TJAM")
    j.add_argument("--paginas", type=int, default=1)
    j.add_argument("--mostrar", type=int, default=5)
    pr = sub.add_parser("processo")
    pr.add_argument("numeros", nargs="+")
    pr.add_argument("--ultimos", type=int, default=8)
    i = sub.add_parser("intimacoes")
    i.add_argument("termos")
    i.add_argument("--desde")
    i.add_argument("--tribunal", default="TJAM", help='sigla do tribunal ou "todos"')
    i.add_argument("--paginas", type=int, default=1)
    i.add_argument("--mostrar", type=int, default=5)
    a = p.parse_args()
    {"jurisprudencia": cmd_jurisprudencia, "processo": cmd_processo, "intimacoes": cmd_intimacoes}[a.cmd](a)


if __name__ == "__main__":
    main()
