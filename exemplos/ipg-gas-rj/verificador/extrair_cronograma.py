# -*- coding: utf-8 -*-
"""
Extrai o cronograma da 1ª inspeção periódica de gás (IPG) do Anexo I da
IN AGENERSA nº 113/2024 (texto original, DOERJ 16/01/2024) e aplica, como
regras, as prorrogações das IN nº 136/2025 e nº 149/2026:

  IN 136/2025, art. 1º: prazos que terminaram até 31/07/2025 ou que vencem
                        até 31/12/2025  -> passam a 30/06/2026
                        (§1º: os demais prazos não mudam)
  IN 149/2026, art. 1º: prazos com vencimento em 30/06/2026 -> 23/09/2026

Saída: dados/cronograma_ipg.csv
Compara, localidade a localidade, a REGRA dos arts. 1º (IN 136 e 149) com as
TABELAS republicadas nos Anexos e lista as divergências (lacuna normativa).
O campo fim_vigente adota a tabela publicada; o verificador pode trocar isso
pelo parâmetro "cronograma_prevalece".

Fonte: texto consolidado da IN 113/2024 publicado pela AGENERSA (já com as
alterações das IN 136/2025 e 149/2026 e os respectivos Anexos):
  https://www.rj.gov.br/agenersa/sites/default/files/arquivos_paginas_basicas/IN113_0.pdf

O script aceita o PDF (extrai o texto com a biblioteca pypdf, se instalada) ou um
.txt já extraído, com uma linha "--- página N ---" entre as páginas. O texto da
norma não é versionado neste repositório: baixe-o da fonte oficial.

Uso (a partir da raiz do repositório):
  python exemplos/ipg-gas-rj/verificador/extrair_cronograma.py IN113_0.pdf
  python exemplos/ipg-gas-rj/verificador/extrair_cronograma.py dados/IN113_texto_consolidado.txt
"""
import csv
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

AQUI = Path(__file__).parent
DATA_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

IN136_CORTE = date(2025, 12, 31)
IN136_NOVO_FIM = date(2026, 6, 30)
IN149_ALVO = date(2026, 6, 30)
IN149_NOVO_FIM = date(2026, 9, 23)


def _d(s: str) -> date:
    d, m, a = s.split("/")
    if m == "04" and d == "31":  # erro material no Anexo I original ("31/04/2025")
        d = "30"
    return date(int(a), int(m), int(d))


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


MARCA_IN149 = "INSTRUÇÃO NORMATIVA Nº 149, DE 30 DE JUNHO DE 2026 (Publicada no DOERJ de 08/07/2026"
MARCA_IN136 = "INSTRUÇÃO NORMATIVA Nº 136, DE 13 DE AGOSTO DE 2025 (Publicada no DOERJ de 18/09/2025"
MARCA_ORIG = "PUBLICADA NO DOERJ DE 16/01/2024"


def _linhas(texto: str) -> list[str]:
    return [re.sub(r"\s+", " ", l).strip() for l in texto.splitlines() if l.strip()]


def tokens_tabela(texto: str, marca_ini: str, marca_fim: str | None) -> list[str]:
    """Tokens de uma das 3 tabelas do texto consolidado (uma data por token)."""
    linhas = _linhas(texto)
    ini = max(i for i, l in enumerate(linhas) if l.startswith(marca_ini) or marca_ini in l)
    fim = len(linhas) if marca_fim is None else next(
        i for i, l in enumerate(linhas) if i > ini and (l.startswith(marca_fim) or marca_fim in l))
    lixo = re.compile(r"^(--- página|INSTRUÇÃO NORMATIVA|\d{1,2}$|CRONOGRAMA|ANEXO I$|PUBLICADA|Altera|\(sessenta\)|estabelecendo|de junho|ÁREA DE|PLANEJAMENTO|ADMINISTRATIVA|BAIRROS|INÍCIO|FIM|CONCESSIONÁRIA|REGIÃO$|MUNICÍPIO|Concessionária|Região|AP$|Bairro|Início|Fim|AP's|Municípios|Bairros)")
    toks = []
    for l in linhas[ini + 1:fim]:
        if lixo.match(l):
            continue
        # "01/01/2025 31/04/2025" ou "Recreio dos Bandeirantes 01/07/2024 23/09/2026"
        partes = re.split(r"\s+(?=\d{2}/\d{2}/\d{4})", l)
        toks.extend(p.strip() for p in partes if p.strip())
    return toks


def parse_tabela(toks: list[str]) -> list[dict]:
    linhas, buf, i = [], [], 0
    while i < len(toks):
        t = toks[i]
        if DATA_RE.match(t) and i + 1 < len(toks) and DATA_RE.match(toks[i + 1]):
            ks = [j for j, x in enumerate(buf) if x in ("CEG", "CEG RIO")]
            k = ks[-1] if ks else 0
            conc = buf[k] if ks else "?"
            meio, local = buf[k + 1:-1], buf[-1]
            eh_bairro_rio = conc == "CEG" and any(re.match(r"^AP ?\d", x) for x in meio)
            if "RIO DE JANEIRO" in meio:      # formato da IN 136: AP / município / bairro
                eh_bairro_rio = True
            linhas.append({
                "concessionaria": conc,
                "regiao": " ".join(x for x in meio if x != "RIO DE JANEIRO"),
                "municipio": "RIO DE JANEIRO" if eh_bairro_rio else local,
                "bairro": local if eh_bairro_rio and local != "Todos" else "*",
                "inicio": _d(t),
                "fim": _d(toks[i + 1]),
            })
            buf, i = [], i + 2
            continue
        buf.append(t)
        i += 1
    return linhas


def chave(r: dict) -> str:
    return norm(r["bairro"] if r["bairro"] != "*" else r["municipio"]).replace("PCA ", "PRACA ")


def extrair(texto: str) -> tuple[list[dict], list[str]]:
    orig = parse_tabela(tokens_tabela(texto, MARCA_ORIG, None))
    t136 = parse_tabela(tokens_tabela(texto, MARCA_IN136, MARCA_ORIG))
    t149 = parse_tabela(tokens_tabela(texto, MARCA_IN149, MARCA_IN136))
    i136 = {chave(r): r for r in t136}
    i149 = {chave(r): r for r in t149}
    avisos, saida = [], []
    for r in orig:
        k = chave(r)
        fim_orig = r["fim"]
        # (a) regra literal do art. 1º da IN 136 + art. 1º da IN 149
        fim_regra = IN136_NOVO_FIM if fim_orig <= IN136_CORTE else fim_orig
        fim_regra = IN149_NOVO_FIM if fim_regra == IN149_ALVO else fim_regra
        # (b) tabela republicada no Anexo da IN 136, + regra da IN 149
        fim_tab = i136[k]["fim"] if k in i136 else None
        if fim_tab is not None and fim_tab == IN149_ALVO:
            fim_tab = IN149_NOVO_FIM
        if k in i149:
            fim_tab = i149[k]["fim"]
        vig = fim_tab if fim_tab is not None else fim_regra
        base = ("Anexo IN 149/2026" if k in i149 else
                "Anexo IN 136/2025" if k in i136 else "regra arts. IN 136/149")
        if fim_tab is not None and fim_tab != fim_regra:
            avisos.append(f"{r['bairro'] if r['bairro'] != '*' else r['municipio']}: "
                          f"original {fim_orig:%d/%m/%Y}; pela regra do art. 1º -> {fim_regra:%d/%m/%Y}; "
                          f"pela tabela publicada -> {fim_tab:%d/%m/%Y}")
        saida.append({
            "concessionaria": r["concessionaria"], "regiao": r["regiao"],
            "municipio": r["municipio"], "bairro": r["bairro"],
            "inicio": r["inicio"], "fim_original_in113": fim_orig,
            "fim_pela_regra": fim_regra, "fim_pela_tabela": fim_tab or "",
            "fim_vigente": vig, "fundamento_fim": base,
            "divergente": "SIM" if fim_tab is not None and fim_tab != fim_regra else "",
        })
    faltando = sorted(set(i136) - {chave(r) for r in orig})
    for k in faltando:
        avisos.append(f"{k}: consta do Anexo da IN 136 mas não do Anexo I original da IN 113")
    return saida, avisos


URL_IN113 = "https://www.rj.gov.br/agenersa/sites/default/files/arquivos_paginas_basicas/IN113_0.pdf"


def ler_texto(src: Path) -> str:
    """Lê o texto da IN 113 a partir do PDF oficial ou de um .txt já extraído."""
    if src.suffix.lower() != ".pdf":
        return src.read_text(encoding="utf-8")
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("Para ler o PDF, instale a biblioteca pypdf (pip install pypdf) "
                 "ou informe um .txt já extraído.")
    paginas = PdfReader(str(src)).pages
    return "\n".join(f"--- página {n} ---\n{pg.extract_text() or ''}" for n, pg in enumerate(paginas, 1))


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "dados" / "IN113_texto_consolidado.txt"
    if not src.exists():
        sys.exit(f"Arquivo não encontrado: {src}\n"
                 f"Baixe o texto consolidado da IN 113/2024 em {URL_IN113}\n"
                 "e informe o caminho do PDF (ou do .txt extraído) como argumento.")
    texto = ler_texto(src)
    linhas, avisos = extrair(texto)
    out = AQUI / "dados" / "cronograma_ipg.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        for r in linhas:
            w.writerow({k: (v.isoformat() if isinstance(v, date) else v) for k, v in r.items()})
    print(f"{len(linhas)} localidades -> {out}")
    from collections import Counter
    for (fim, base), n in sorted(Counter((r['fim_vigente'], r['fundamento_fim']) for r in linhas).items()):
        print(f"  fim {fim:%d/%m/%Y} ({base}): {n}")
    print(f"Divergências regra × tabela publicada: {len(avisos)}")
    for a in avisos:
        print("  -", a)


if __name__ == "__main__":
    main()
