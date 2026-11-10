# -*- coding: utf-8 -*-
"""
Gera um envio sintético válido a partir dos `exemplo` dos campos do contrato.

Heurística (3 registros por bloco):
  - cada campo parte do seu `exemplo` (ou de um valor genérico do tipo, se não houver);
  - datas e datas-hora do registro i são deslocadas i dias, preservando a ordem entre elas;
  - campos de chave variam por registro (sufixo numérico, novo dígito verificador, próximo
    valor do domínio etc.) para respeitar a R02;
  - campos com `referencia` recebem valores existentes no bloco referenciado (R03);
  - `data_referencia` é a maior data de evento gerada; `totais` conferem com a contagem (R08).

Regras `expressao` e `condicional` dependem do conteúdo dos exemplos; por isso gerar_padrao.py
valida o envio gerado e avisa se ele não for aceito.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta
from typing import Any

from contrato import Campo, Contrato, completar_cnpj, completar_cpf, para_data, problema_valor

REGISTROS_POR_BLOCO = 3
DATA_PADRAO = "2026-01-15"


def _valor_generico(c: Campo) -> Any:
    t = c.tipo
    if t == "texto":
        for cand in ("EXEMPLO-1", "EX1", "00000001", "1", "A", "a"):
            cand2 = cand[: c.tamanho_max] if c.tamanho_max else cand
            if problema_valor(c, cand2) is None:
                return cand2
        return "EXEMPLO"
    if t == "inteiro":
        return int(c.minimo) if c.minimo is not None else 1
    if t == "decimal":
        return float(c.minimo) if c.minimo is not None else 1.5
    if t == "data":
        return DATA_PADRAO
    if t == "data_hora":
        return DATA_PADRAO + "T10:00:00-03:00"
    if t == "booleano":
        return True
    if t == "enum":
        return (c.dominio or ["?"])[0]
    if t == "cnpj":
        return completar_cnpj("112223330001")
    if t == "cpf":
        return completar_cpf("123456789")
    if t == "cpf_cnpj":
        return completar_cpf("123456789")
    if t == "cep":
        return "20000000"
    if t == "ibge_municipio":
        return "3304557"
    if t == "url":
        return "https://documentos.exemplo.invalid/arquivo-1"
    if t == "sha256":
        return hashlib.sha256(b"exemplo").hexdigest()
    return None  # pragma: no cover


def _base(c: Campo) -> Any:
    return c.exemplo if c.exemplo is not None else _valor_generico(c)


def _somar_digitos(s: str, i: int) -> str:
    m = re.search(r"(\d+)$", s)
    if not m:
        return s
    n = str(int(m.group(1)) + i).zfill(len(m.group(1)))[-len(m.group(1)):]
    return s[: m.start()] + n


def _variar(c: Campo, v: Any, i: int) -> Any:
    """Valor distinto para o registro i (usado nos campos de chave)."""
    if i == 0:
        return v
    t = c.tipo
    if t in ("texto", "url"):
        s = str(v)
        candidatos = [_somar_digitos(s, i), f"{s}{i + 1}", f"{s}-{i + 1}", s[:-1] + str(i) if s else str(i)]
        for cand in candidatos:
            if cand != s and problema_valor(c, cand) is None:
                return cand
        return v
    if t == "inteiro":
        cand = v + i
        return cand if c.maximo is None or cand <= c.maximo else v - i
    if t == "decimal":
        cand = v + i
        return cand if c.maximo is None or cand <= c.maximo else v - i
    if t == "enum":
        dom = c.dominio or [v]
        return dom[(dom.index(v) + i) % len(dom)] if v in dom else v
    if t == "cnpj" or (t == "cpf_cnpj" and len(str(v)) == 14):
        return completar_cnpj(str(int(str(v)[:12]) + i).zfill(12)[-12:])
    if t in ("cpf", "cpf_cnpj"):
        return completar_cpf(str(int(str(v)[:9]) + i).zfill(9)[-9:])
    if t in ("cep", "ibge_municipio"):
        return _somar_digitos(str(v), i)
    if t == "sha256":
        return hashlib.sha256(f"{v}{i}".encode()).hexdigest()
    return v


def _deslocar(c: Campo, v: Any, dias: int) -> Any:
    if dias == 0 or not isinstance(v, str):
        return v
    if c.tipo == "data":
        d = para_data(v)
        return (d + timedelta(days=dias)).isoformat() if d else v
    if c.tipo == "data_hora":
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return v
        s = (dt + timedelta(days=dias)).isoformat()
        return s.replace("+00:00", "Z") if v.endswith("Z") else s
    return v


def gerar_exemplo(contrato: Contrato, n: int = REGISTROS_POR_BLOCO) -> dict:
    """Monta o envio sintético (carga COMPLETA) a partir dos exemplos do contrato."""
    blocos: dict[str, list[dict]] = {}
    for b in contrato.blocos:
        registros = []
        for i in range(n):
            reg: dict[str, Any] = {}
            for c in b.campos:
                if c.referencia:
                    continue
                v = _deslocar(c, _base(c), i)
                if c.nome in b.chave:
                    v = _variar(c, v, i)
                reg[c.nome] = v
            registros.append(reg)
        blocos[b.nome] = registros

    # referências: aponta para registros existentes do bloco referenciado
    for b in contrato.blocos:
        for c in b.campos:
            if not c.referencia:
                continue
            alvo_b, alvo_c = c.referencia.split(".", 1)
            alvo = blocos.get(alvo_b) or []
            for i, reg in enumerate(blocos[b.nome]):
                if alvo and alvo[i % len(alvo)].get(alvo_c) is not None:
                    reg[c.nome] = alvo[i % len(alvo)][alvo_c]
                else:
                    reg[c.nome] = _base(c)

    # remove registros com chave repetida (quando a variação não bastou)
    for b in contrato.blocos:
        if not b.chave:
            continue
        vistos, unicos = set(), []
        for reg in blocos[b.nome]:
            k = tuple(str(reg.get(x)) for x in b.chave)
            if k not in vistos:
                vistos.add(k)
                unicos.append(reg)
        blocos[b.nome] = unicos

    # data de referência: a maior data de evento gerada (ou a maior data, ou uma data fixa)
    def datas(somente_evento: bool) -> list[date]:
        res = []
        grupos = [(contrato.cabecalho_contrato, [{c.nome: _base(c) for c in contrato.cabecalho_contrato}])]
        grupos += [(b.campos, blocos[b.nome]) for b in contrato.blocos]
        for campos, regs in grupos:
            for c in campos:
                if c.tipo in ("data", "data_hora") and (c.evento or not somente_evento):
                    res += [d for d in (para_data(r.get(c.nome)) for r in regs) if d]
        return res

    candidatas = datas(True) or datas(False)
    data_ref = max(candidatas) if candidatas else date.fromisoformat(DATA_PADRAO)

    envio: dict[str, Any] = {}
    for c in contrato.cabecalho:
        if c.nome == "data_referencia":
            envio[c.nome] = data_ref.isoformat()
        elif c.nome == "data_referencia_anterior":
            continue
        elif c.nome == "gerado_em":
            envio[c.nome] = (data_ref + timedelta(days=1)).isoformat() + "T08:00:00-03:00"
        else:
            envio[c.nome] = _base(c)
    envio["totais"] = {b.nome: len(blocos[b.nome]) for b in contrato.blocos}
    return {"envio": envio, **blocos}
