# -*- coding: utf-8 -*-
"""
Converte a planilha preenchida (modelo gerado por gerar_padrao.py) no JSON do envio.

A conversão usa o mesmo contrato de coleta que gerou a planilha e é deliberadamente
tolerante: ela não rejeita nada sozinha. Valores que não puderem ser convertidos são
mantidos como estão, para que o validador os aponte (R01) com a célula de origem.

Regras de conversão:
  - célula vazia → campo omitido;
  - '-', 'N/A', 'NA', 'N/D', 'NULL' → campo omitido, com aviso (deixe a célula vazia);
  - fórmula → usa o valor calculado gravado pelo Excel, com aviso; sem valor calculado, omitido;
  - booleano: SIM/NAO → true/false;
  - data: célula de data → AAAA-MM-DD; texto DD/MM/AAAA → AAAA-MM-DD, com aviso;
  - data_hora: texto ISO 8601 com fuso (célula de data e hora sem fuso fica sem fuso e é rejeitada);
  - inteiro/decimal: número; texto numérico (aceita vírgula decimal) → número, com aviso;
  - CNPJ, CPF, CEP: pontuação removida, com aviso; célula numérica → texto, com aviso;
  - `totais.<bloco>` vazio na aba envio → preenchido com a contagem real, com aviso;
  - `contrato`, `versao_layout` e `gerado_em` vazios → preenchidos pela ferramenta, com aviso.

Uso como biblioteca:
    from excel_para_json import converter_excel
    documento, avisos, celulas = converter_excel("envio.xlsx", contrato)

Uso pela linha de comando (só converte, sem validar; para validar use validar_envio.py):
    python ferramentas/excel_para_json.py contrato.yaml envio.xlsx -o envio.json
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from contrato import TIPOS_DOCUMENTO, Campo, Contrato, ErroContrato, carregar_contrato

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover
    load_workbook = None

VAZIOS_PROIBIDOS = {"-", "--", "N/A", "NA", "N/D", "ND", "NULL", "NONE", "#N/D", "#N/A"}
RE_DATA_BR = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
RE_DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_NUMERO = re.compile(r"^-?\d+([.,]\d+)?$")

ABA_ENVIO = "envio"
PREFIXO_TOTAIS = "totais."


class ErroPlanilha(Exception):
    """A planilha não pôde ser lida (arquivo corrompido, abas ausentes etc.)."""


def _omitido(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def converter_celula(c: Campo, v: Any, onde: str, avisos: list[str]) -> tuple[bool, Any]:
    """Converte o valor bruto da célula. Devolve (presente, valor)."""
    if _omitido(v):
        return False, None
    if isinstance(v, str):
        v = v.strip()
        if v.upper() in VAZIOS_PROIBIDOS:
            avisos.append(f"{onde}: '{v}' tratado como vazio; deixe a célula em branco quando não houver informação")
            return False, None
    t = c.tipo

    if t == "booleano":
        if isinstance(v, bool):
            return True, v
        s = str(v).strip().upper()
        if s == "SIM":
            return True, True
        if s in ("NAO", "NÃO"):
            return True, False
        return True, v

    if t == "data":
        if isinstance(v, datetime):
            if v.time() != datetime.min.time():
                avisos.append(f"{onde}: a célula tem hora; usada só a data")
            return True, v.date().isoformat()
        if isinstance(v, date):
            return True, v.isoformat()
        if isinstance(v, str):
            m = RE_DATA_BR.match(v)
            if m:
                iso = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                avisos.append(f"{onde}: data digitada como texto ({v}); convertida para {iso}. "
                              "Prefira célula de data")
                return True, iso
            return True, v
        return True, v

    if t == "data_hora":
        if isinstance(v, datetime):
            if v.tzinfo is None:
                avisos.append(f"{onde}: data e hora sem fuso horário; digite como texto, "
                              "ex.: 2026-01-31T18:00:00-03:00")
                return True, v.replace(microsecond=0).isoformat()
            return True, v.isoformat()
        return True, v if not isinstance(v, str) else v.strip()

    if t in ("inteiro", "decimal"):
        if isinstance(v, bool):
            return True, v
        if isinstance(v, (int, float)):
            if t == "inteiro" and isinstance(v, float) and v.is_integer():
                return True, int(v)
            return True, v
        if isinstance(v, str) and RE_NUMERO.match(v):
            n = float(v.replace(",", "."))
            avisos.append(f"{onde}: número digitado como texto ({v}); convertido")
            if t == "inteiro" and n.is_integer() and "," not in v and "." not in v:
                return True, int(n)
            return True, n
        return True, v

    # tipos textuais
    numerico = isinstance(v, (int, float)) and not isinstance(v, bool)
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    if isinstance(v, (datetime, date)):
        return True, v.isoformat()
    s = str(v).strip() if not isinstance(v, bool) else v
    if not isinstance(s, str):
        return True, s
    if numerico and t != "texto" and t != "enum":
        avisos.append(f"{onde}: célula numérica em campo de texto; formate a coluna como texto "
                      "para não perder zeros à esquerda")
    if t in TIPOS_DOCUMENTO or t == "cep":
        limpo = re.sub(r"[.\-/\s]", "", s)
        if limpo != s:
            avisos.append(f"{onde}: pontuação removida ({s} → {limpo}); informe só os dígitos")
            s = limpo
    if t == "sha256":
        s = s.lower()
    return True, s


def _abrir(origem: str | Path | bytes):
    if load_workbook is None:  # pragma: no cover
        raise ErroPlanilha("a biblioteca openpyxl não está instalada (pip install --user openpyxl)")
    try:
        if isinstance(origem, (bytes, bytearray)):
            wf = load_workbook(io.BytesIO(origem), data_only=False)
            wv = load_workbook(io.BytesIO(origem), data_only=True)
        else:
            wf = load_workbook(origem, data_only=False)
            wv = load_workbook(origem, data_only=True)
    except Exception as e:  # openpyxl levanta exceções variadas para arquivos corrompidos
        raise ErroPlanilha(f"não foi possível abrir a planilha ({type(e).__name__}: {e})") from None
    return wf, wv


def _valor(wf, wv, aba: str, linha: int, coluna: int, onde: str, avisos: list[str]) -> Any:
    bruto = wf[aba].cell(row=linha, column=coluna).value
    if isinstance(bruto, str) and bruto.startswith("="):
        calc = wv[aba].cell(row=linha, column=coluna).value
        if calc is None:
            avisos.append(f"{onde}: fórmula sem valor calculado ({bruto}); campo omitido. "
                          "Cole os dados como valores")
            return None
        avisos.append(f"{onde}: fórmula ({bruto}); usado o valor calculado {calc!r}. "
                      "Prefira colar os dados como valores")
        return calc
    return bruto


def converter_excel(origem: str | Path | bytes, contrato: Contrato) -> tuple[dict, list[str], dict]:
    """Converte a planilha no documento JSON do envio.

    Devolve (documento, avisos, celulas), em que `celulas` mapeia
    (bloco, índice, campo) → 'aba!A1' para o relatório apontar a célula de origem
    (bloco 'envio' com índice None para o cabeçalho).
    """
    wf, wv = _abrir(origem)
    avisos: list[str] = []
    celulas: dict[tuple, str] = {}
    abas = set(wf.sheetnames)

    # ---- cabeçalho
    envio: dict[str, Any] = {}
    totais: dict[str, Any] = {}
    if ABA_ENVIO not in abas:
        raise ErroPlanilha(f"a planilha não tem a aba '{ABA_ENVIO}'; use o modelo gerado para o contrato "
                           f"{contrato.contrato} {contrato.versao}")
    ws = wf[ABA_ENVIO]
    cab = [str(c.value).strip().lower() if c.value is not None else "" for c in ws[1]]
    try:
        col_campo = cab.index("campo") + 1
        col_valor = cab.index("valor") + 1
    except ValueError:
        raise ErroPlanilha("a aba 'envio' deve ter as colunas 'campo' e 'valor' na linha 1") from None
    campos_cab = {c.nome: c for c in contrato.cabecalho}
    vistos: set[str] = set()
    for linha in range(2, ws.max_row + 1):
        nome = ws.cell(row=linha, column=col_campo).value
        if _omitido(nome):
            continue
        nome = str(nome).strip()
        letra = ws.cell(row=linha, column=col_valor).column_letter
        onde = f"envio!{letra}{linha}"
        bruto = _valor(wf, wv, ABA_ENVIO, linha, col_valor, onde, avisos)
        if nome.startswith(PREFIXO_TOTAIS):
            bloco = nome[len(PREFIXO_TOTAIS):]
            if bloco not in contrato.nomes_blocos:
                avisos.append(f"{onde}: linha '{nome}' não corresponde a nenhum bloco; ignorada")
                continue
            if not _omitido(bruto):
                if isinstance(bruto, float) and bruto.is_integer():
                    bruto = int(bruto)
                if isinstance(bruto, str) and bruto.strip().isdigit():
                    bruto = int(bruto.strip())
                totais[bloco] = bruto
                celulas[("envio", None, f"totais.{bloco}")] = onde
            continue
        c = campos_cab.get(nome)
        if c is None:
            avisos.append(f"{onde}: campo '{nome}' não existe no cabeçalho do contrato; ignorado")
            continue
        vistos.add(nome)
        presente, valor = converter_celula(c, bruto, onde, avisos)
        if presente:
            envio[nome] = valor
            celulas[("envio", None, nome)] = onde
    faltam = [c.nome for c in contrato.cabecalho if c.nome not in vistos]
    if faltam:
        avisos.append(f"aba envio: linha(s) ausente(s) para {', '.join(faltam)}")

    # ---- blocos
    documento: dict[str, Any] = {"envio": envio}
    for b in contrato.blocos:
        registros: list[dict] = []
        documento[b.nome] = registros
        if b.nome not in abas:
            avisos.append(f"a planilha não tem a aba '{b.nome}'; bloco considerado vazio")
            continue
        ws = wf[b.nome]
        cabecalho = {}
        for cel in ws[1]:
            if cel.value is None:
                continue
            nome = str(cel.value).strip()
            if nome in cabecalho:
                avisos.append(f"{b.nome}!{cel.coordinate}: coluna '{nome}' repetida; usada a primeira")
                continue
            cabecalho[nome] = cel.column
        desconhecidas = [n for n in cabecalho if b.campo(n) is None]
        for n in desconhecidas:
            avisos.append(f"aba {b.nome}: coluna '{n}' não existe no contrato; ignorada")
        ausentes = [c.nome for c in b.campos if c.nome not in cabecalho]
        if ausentes:
            avisos.append(f"aba {b.nome}: coluna(s) ausente(s): {', '.join(ausentes)}")
        mapa = [(b.campo(n), col) for n, col in cabecalho.items() if b.campo(n) is not None]
        for linha in range(2, ws.max_row + 1):
            brutos = []
            for c, col in mapa:
                letra = ws.cell(row=linha, column=col).column_letter
                onde = f"{b.nome}!{letra}{linha}"
                brutos.append((c, onde, _valor(wf, wv, b.nome, linha, col, onde, avisos)))
            if all(_omitido(v) for _, _, v in brutos):
                continue
            reg: dict[str, Any] = {}
            idx = len(registros)
            for c, onde, v in brutos:
                presente, valor = converter_celula(c, v, onde, avisos)
                if presente:
                    reg[c.nome] = valor
                    celulas[(b.nome, idx, c.nome)] = onde
            registros.append(reg)

    # ---- campos que a ferramenta preenche
    for c in contrato.cabecalho_automatico:
        if c.constante is not None and c.nome not in envio:
            envio[c.nome] = c.constante
            avisos.append(f"envio: {c.nome} vazio; preenchido com {c.constante}")
    if "gerado_em" not in envio:
        envio["gerado_em"] = datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()
        avisos.append("envio: gerado_em vazio; preenchido com o momento da conversão")
    for b in contrato.blocos:
        if b.nome not in totais:
            totais[b.nome] = len(documento[b.nome])
            avisos.append(f"envio: totais.{b.nome} vazio; preenchido com a contagem real ({totais[b.nome]})")
    envio["totais"] = {b.nome: totais[b.nome] for b in contrato.blocos}
    return documento, avisos, celulas


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:  # pragma: no cover
            pass
    ap = argparse.ArgumentParser(description="Converte a planilha preenchida no JSON do envio (sem validar).")
    ap.add_argument("contrato", type=Path, help="caminho do contrato.yaml")
    ap.add_argument("planilha", type=Path, help="planilha .xlsx preenchida")
    ap.add_argument("-o", "--saida", type=Path, help="arquivo JSON de saída (padrão: mesmo nome, .json)")
    args = ap.parse_args(argv)
    try:
        contrato = carregar_contrato(args.contrato)
        doc, avisos, _ = converter_excel(args.planilha, contrato)
    except (ErroContrato, ErroPlanilha) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    saida = args.saida or args.planilha.with_suffix(".json")
    saida.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for a in avisos:
        print(f"aviso: {a}")
    print(f"JSON gravado em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
