# -*- coding: utf-8 -*-
"""
Gera o JSON Schema (draft 2020-12) do envio a partir do contrato de coleta.

Estrutura gerada:
  - raiz: objeto com `envio` e uma propriedade por bloco (lista de registros);
  - `$defs`: `Envio`, `Totais` e um `$def` por bloco, com o nome do bloco;
  - `additionalProperties: false` em todos os objetos;
  - campos opcionais aceitam `null`; campos obrigatórios não;
  - obrigatoriedade condicional e `INCREMENTAL → data_referencia_anterior` como `if/then`,
    marcados com `$comment` iniciado por "R05" (o validador usa a marca para classificar o erro).

O que o schema não expressa (chave única, referência entre blocos, datas de evento em relação
à data de referência, dígito verificador de CNPJ/CPF, totais e regras do contrato) é aplicado
pelo validador (validar_envio.py).
"""
from __future__ import annotations

from typing import Any

from contrato import PADRAO_TIPO, Campo, Condicao, Contrato

DIALETO = "https://json-schema.org/draft/2020-12/schema"


def nome_def_bloco(bloco: str) -> str:
    return bloco


def schema_valor(c: Campo) -> dict[str, Any]:
    """Schema do valor de um campo (sem a alternativa null)."""
    t = c.tipo
    s: dict[str, Any] = {"title": c.nome}
    if c.descricao:
        s["description"] = c.descricao
    if t == "texto":
        s["type"] = "string"
        s["minLength"] = 1
        if c.tamanho_max:
            s["maxLength"] = c.tamanho_max
        if c.formato:
            s["pattern"] = c.formato
    elif t == "inteiro":
        s["type"] = "integer"
    elif t == "decimal":
        s["type"] = "number"
    elif t == "data":
        s.update(type="string", pattern=PADRAO_TIPO["data"], format="date")
    elif t == "data_hora":
        s.update(type="string", pattern=PADRAO_TIPO["data_hora"], format="date-time")
    elif t == "booleano":
        s["type"] = "boolean"
    elif t == "enum":
        s["type"] = "string"
        s["enum"] = list(c.dominio or [])
    elif t == "url":
        s.update(type="string", pattern=PADRAO_TIPO["url"], format="uri")
    else:  # cnpj, cpf, cpf_cnpj, cep, ibge_municipio, sha256
        s.update(type="string", pattern=PADRAO_TIPO[t])
    if t in ("inteiro", "decimal"):
        if c.minimo is not None:
            s["minimum"] = c.minimo
        if c.maximo is not None:
            s["maximum"] = c.maximo
    if c.constante is not None:
        s["const"] = c.constante
    if c.exemplo is not None:
        s["examples"] = [c.exemplo]
    return s


def schema_campo(c: Campo) -> dict[str, Any]:
    valor = schema_valor(c)
    if c.obrigatorio is True:
        return valor
    # opcional ou condicional: aceita null (o if/then do registro exige o valor quando aplicável)
    return {
        "title": valor.get("title"),
        **({"description": valor["description"]} if "description" in valor else {}),
        "anyOf": [{k: v for k, v in valor.items() if k not in ("title", "description")}, {"type": "null"}],
    }


def schema_condicao(cond: Condicao) -> dict[str, Any]:
    """`if` de JSON Schema equivalente a Condicao.avaliar()."""
    campo = cond.campo
    if cond.operador == "preenchido":
        if cond.valor:
            return {"required": [campo], "properties": {campo: {"not": {"type": "null"}}}}
        return {"anyOf": [{"not": {"required": [campo]}}, {"properties": {campo: {"type": "null"}}}]}
    if cond.operador == "igual":
        return {"required": [campo], "properties": {campo: {"const": cond.valor}}}
    if cond.operador == "diferente":
        return {"required": [campo], "properties": {campo: {"not": {"enum": [cond.valor, None]}}}}
    return {"required": [campo], "properties": {campo: {"enum": list(cond.valor)}}}


def schema_obrigatoriedade_condicional(c: Campo) -> dict[str, Any]:
    cond = c.obrigatorio
    assert isinstance(cond, Condicao)
    return {
        "$comment": f"R05: {c.nome} é obrigatório quando {cond.texto()}",
        "if": schema_condicao(cond),
        "then": {"required": [c.nome], "properties": {c.nome: {"not": {"type": "null"}}}},
    }


def schema_objeto(campos: list[Campo], titulo: str, descricao: str) -> dict[str, Any]:
    s: dict[str, Any] = {
        "title": titulo,
        "type": "object",
        "additionalProperties": False,
        "required": [c.nome for c in campos if c.obrigatorio is True],
        "properties": {c.nome: schema_campo(c) for c in campos},
    }
    if descricao:
        s["description"] = descricao
    condicionais = [schema_obrigatoriedade_condicional(c) for c in campos if isinstance(c.obrigatorio, Condicao)]
    if condicionais:
        s["allOf"] = condicionais
    return s


def gerar_schema(contrato: Contrato) -> dict[str, Any]:
    """Monta o JSON Schema 2020-12 do envio descrito pelo contrato."""
    blocos = contrato.blocos
    totais = {
        "title": "Totais para conferência",
        "description": "Quantidade de registros de cada bloco neste envio; deve ser igual à contagem real (R08).",
        "type": "object",
        "additionalProperties": False,
        "required": [b.nome for b in blocos],
        "properties": {
            b.nome: {"title": f"Total de {b.nome}", "type": "integer", "minimum": 0} for b in blocos
        },
    }
    envio = schema_objeto(contrato.cabecalho, "Cabeçalho do envio",
                          "Identifica o contrato, quem envia, a data de corte e o tipo de carga.")
    envio["required"] = envio["required"] + ["totais"]
    envio["properties"]["totais"] = {"$ref": "#/$defs/Totais"}

    defs: dict[str, Any] = {"Envio": envio, "Totais": totais}
    for b in blocos:
        defs[nome_def_bloco(b.nome)] = schema_objeto(b.campos, b.nome, b.descricao)

    propriedades: dict[str, Any] = {"envio": {"$ref": "#/$defs/Envio"}}
    for b in blocos:
        propriedades[b.nome] = {
            "title": b.nome,
            **({"description": b.descricao} if b.descricao else {}),
            "type": "array",
            "items": {"$ref": f"#/$defs/{nome_def_bloco(b.nome)}"},
        }

    descricao = contrato.descricao or contrato.titulo
    return {
        "$schema": DIALETO,
        "$id": f"urn:padrao-coleta:{contrato.contrato}:{contrato.versao}",
        "title": f"{contrato.titulo} — envio, layout {contrato.versao}",
        "description": (
            f"{descricao} Gerado a partir do contrato de coleta {contrato.contrato} versão {contrato.versao}. "
            "Chave única, referências entre blocos, datas de evento, dígitos verificadores, totais e as "
            "regras adicionais do contrato são conferidos pelo validador (validar_envio.py)."
        ).strip(),
        "type": "object",
        "additionalProperties": False,
        "required": ["envio"] + [b.nome for b in blocos],
        "properties": propriedades,
        "$defs": defs,
    }
