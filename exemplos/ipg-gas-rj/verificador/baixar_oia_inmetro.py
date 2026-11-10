# -*- coding: utf-8 -*-
"""
Baixa da consulta pública da Cgcre/Inmetro os Organismos de Inspeção acreditados
na categoria OIA-IG (instalações prediais de gás combustível) e grava
dados/oia_inmetro.csv no formato de habilitacoes.csv do verificador.

Limite da fonte: a consulta mostra só a SITUAÇÃO ATUAL (Ativo / Suspenso /
Cancelado) e a data dessa situação. Não há histórico de suspensões. Por isso:
  inicio = data de concessão da acreditação
  fim    = data da situação, quando Suspenso/Cancelado (vazio se Ativo)
Uma suspensão já encerrada não aparece — ver lacuna L10.

O arquivo baixado não é versionado neste repositório (ver .gitignore): cada
usuário gera a sua cópia, com a data da consulta.

Uso (a partir da raiz do repositório):
  python exemplos/ipg-gas-rj/verificador/baixar_oia_inmetro.py
"""
import csv
import html
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

URL = "http://www.inmetro.gov.br/organismos/"
TIPO = "31"  # OIA-IG
AQUI = Path(__file__).parent


def post(pagina: str, campos: dict) -> str:
    req = urllib.request.Request(URL + pagina, data=urllib.parse.urlencode(campos).encode(),
                                 headers={"User-Agent": "verificador-autovistoria/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("latin-1")


def texto(h: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def listar() -> list[dict]:
    regs, pag = [], 1
    while True:
        h = post("resultado_consulta.asp", {"Seq_Tipo_Relacionamento": TIPO, "vPagina": pag,
                                             "vPaginaIni": 1, "vPaginaFim": 10})
        linhas = re.findall(r"<tr>\s*(<td class=\"listagem\".*?)</tr>", h, flags=re.S)
        novos = 0
        for l in linhas:
            cel = [texto(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", l, flags=re.S)]
            m = re.search(r"Detalhes\((\d+),", l)
            if len(cel) < 10 or not m:
                continue
            regs.append({"numero": f"{cel[0]}-{cel[1]}", "nome": cel[2], "uf": cel[5], "cidade": cel[6],
                         "situacao": cel[8], "data_situacao": cel[9], "seq": m.group(1)})
            novos += 1
        total = re.search(r"de\s*(?:&nbsp;)?\s*(\d+)", texto(h).split("Resultados", 1)[-1])
        if not novos or (total and len(regs) >= int(total.group(1))):
            return regs
        pag += 1
        time.sleep(0.5)


def detalhe(seq: str) -> dict:
    t = texto(post("detalhe.asp", {"hSeq_Cliente": seq, "hSeq_Tipo_Relacionamento": TIPO}))
    cnpj = re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", t)
    conc = re.search(r"Concess[aã]o[^0-9]{0,40}(\d{2}/\d{2}/\d{4})", t)
    return {"cnpj": cnpj.group(0) if cnpj else "", "data_concessao": conc.group(1) if conc else "", "_texto": t}


def main():
    regs = listar()
    print(f"{len(regs)} organismos OIA-IG na lista")
    out = AQUI / "dados" / "oia_inmetro.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["doc_inspetora", "tipo", "numero", "inicio", "fim", "situacao", "nome"])
        for r in regs:
            dt = detalhe(r["seq"])
            time.sleep(0.3)
            ini = "-".join(reversed(dt["data_concessao"].split("/"))) if dt["data_concessao"] else ""
            fim = ""
            if r["situacao"].startswith(("Suspenso", "Cancelado")) and re.match(r"\d{2}/\d{2}/\d{4}", r["data_situacao"]):
                fim = "-".join(reversed(r["data_situacao"].split("/")))
            w.writerow([dt["cnpj"], "OIA_INMETRO", r["numero"], ini, fim, r["situacao"], r["nome"]])
            if not dt["cnpj"] or not ini:
                print("  ! detalhe incompleto:", r["numero"], dt["_texto"][:200])
    print("->", out)


if __name__ == "__main__":
    main()
