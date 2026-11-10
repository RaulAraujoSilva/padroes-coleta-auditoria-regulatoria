# -*- coding: utf-8 -*-
"""
Valida um envio (JSON ou Excel) contra o contrato de coleta.

Uso:
  python ferramentas/validar_envio.py contrato.yaml envio.json [--json] [--saida ARQUIVO]
  python ferramentas/validar_envio.py contrato.yaml envio.xlsx [--exportar-json envio.json]

  O envio pode ser .json, .json.gz, .zip (com um ou mais .json, tratados como partes do
  mesmo envio, ou com um .xlsx) ou .xlsx (planilha gerada por gerar_padrao.py e preenchida).

O que é conferido:
  ARQ  arquivo legível, JSON válido, planilha no modelo, partes compatíveis
  R01  obrigatórios presentes; tipo, formato e domínio corretos (JSON Schema gerado em memória)
  R02  chave única dentro do bloco
  R03  referência existe no bloco referenciado (só na carga COMPLETA)
  R04  datas de evento ≤ data_referencia
  R05  obrigatoriedade condicional (inclusive data_referencia_anterior na carga INCREMENTAL)
  R07  dígito verificador de CNPJ e CPF
  R08  totais do cabeçalho = contagem real
  + as regras do contrato (ordem_datas, data_minima, condicional, expressao)

Códigos de saída:
  0  envio aceito (com ou sem alertas)
  1  envio rejeitado
  2  erro de uso (parâmetros, contrato inválido, arquivo inexistente ou de tipo não suportado)
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from contrato import (REGRAS_AUTOMATICAS, TIPOS_DATA, TIPOS_DOCUMENTO, Contrato, ErroContrato,
                      Registro, avaliar_expressao, carregar_contrato, data_hora_valida,
                      documento_valido, para_data)
from gerador_schema import gerar_schema

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover
    Draft202012Validator = None
    FormatChecker = None

VERSAO_VALIDADOR = "1.0.0"
NOME_TIPO_JSON = {"string": "texto", "integer": "número inteiro", "number": "número",
                  "boolean": "booleano (true/false)", "object": "objeto", "array": "lista", "null": "null"}


# --------------------------------------------------------------------------- relatório

@dataclass
class Ocorrencia:
    regra: str
    mensagem: str
    bloco: str | None = None
    chave: str | None = None
    campo: str | None = None
    celula: str | None = None

    def texto(self) -> str:
        local = ""
        if self.bloco:
            local = self.bloco
            if self.chave:
                local += f" ({self.chave})"
            if self.campo:
                local += f" · {self.campo}"
        elif self.campo:
            local = self.campo
        if self.celula:
            local += f" [célula {self.celula}]"
        return f"{local}: {self.mensagem}" if local else self.mensagem

    def como_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None and k != "regra"}


class Relatorio:
    def __init__(self, contrato: Contrato, max_mensagens: int = 50):
        self.contrato = contrato
        self.max = max_mensagens
        self.catalogo: list[tuple[str, str, str]] = (
            [("ARQ", "Arquivo legível e no formato do contrato", "rejeicao")] + contrato.catalogo_regras()
        )
        self.severidade = {rid: sev for rid, _, sev in self.catalogo}
        self.ocorrencias: dict[str, list[Ocorrencia]] = defaultdict(list)
        self.arquivos: list[dict] = []
        self.resumo: dict = {}
        self.avisos_conversao: list[str] = []
        self.observacoes: list[str] = []
        self.celulas: dict = {}

    def add(self, regra: str, mensagem: str, bloco: str | None = None, chave: str | None = None,
            campo: str | None = None, indice: int | None = None) -> None:
        celula = None
        if self.celulas and bloco:
            celula = self.celulas.get((bloco, indice, campo)) if campo else None
        self.ocorrencias[regra].append(Ocorrencia(regra, mensagem, bloco, chave, campo, celula))

    def contagem(self, regra: str) -> int:
        return len(self.ocorrencias.get(regra, []))

    @property
    def rejeitado(self) -> bool:
        return any(self.contagem(r) for r, sev in self.severidade.items() if sev == "rejeicao")

    @property
    def tem_alertas(self) -> bool:
        return any(self.contagem(r) for r, sev in self.severidade.items() if sev == "alerta")

    @property
    def situacao(self) -> str:
        if self.rejeitado:
            return "REJEITADO"
        return "ACEITO COM ALERTAS" if self.tem_alertas else "ACEITO"

    def como_dict(self) -> dict:
        return {
            "validador": f"validar_envio.py {VERSAO_VALIDADOR}",
            "contrato": self.contrato.contrato,
            "versao_layout": self.contrato.versao,
            "situacao": self.situacao,
            "arquivos": self.arquivos,
            "resumo": self.resumo,
            "avisos_conversao": self.avisos_conversao,
            "observacoes": self.observacoes,
            "regras": [
                {
                    "regra": rid, "severidade": sev, "descricao": desc,
                    "ocorrencias": self.contagem(rid),
                    "detalhes": [o.como_dict() for o in self.ocorrencias.get(rid, [])[: self.max]],
                }
                for rid, desc, sev in self.catalogo
            ],
        }

    def como_texto(self) -> str:
        c = self.contrato
        l: list[str] = ["=" * 78, f"VALIDAÇÃO DE ENVIO — {c.titulo} — contrato {c.contrato}, layout {c.versao}",
                        "=" * 78]
        for a in self.arquivos:
            l.append(f"Arquivo: {a['arquivo']}")
            l.append(f"  {a['bytes']:,} bytes".replace(",", ".") + f" | SHA-256 {a['sha256']}")
        r = self.resumo
        if r:
            l.append(f"Remetente: {r.get('remetente')} | data de referência: {r.get('data_referencia')} | "
                     f"carga: {r.get('tipo_carga')}")
            l.append("Registros: " + ", ".join(f"{k} = {v}" for k, v in r.get("contagem", {}).items()))
        if self.avisos_conversao:
            l.append(f"Avisos da conversão da planilha ({len(self.avisos_conversao)}):")
            for a in self.avisos_conversao[: self.max]:
                l.append(f"  - {a}")
            if len(self.avisos_conversao) > self.max:
                l.append(f"  ... e mais {len(self.avisos_conversao) - self.max} aviso(s)")
        for o in self.observacoes:
            l.append(f"Observação: {o}")
        l += ["-" * 78, f"RESULTADO: {self.situacao}", "-" * 78]
        for rid, desc, sev in self.catalogo:
            n = self.contagem(rid)
            if rid == "ARQ" and n == 0:
                continue
            rotulo = "ALERTA" if sev == "alerta" else "REGRA "
            l.append(f"[{rotulo} {rid}] {desc}: {'ok' if n == 0 else f'{n} ocorrência(s)'}")
            for o in self.ocorrencias.get(rid, [])[: self.max]:
                l.append(f"      - {o.texto()}")
            if n > self.max:
                l.append(f"      ... e mais {n - self.max} ocorrência(s) não exibida(s)")
        l.append("=" * 78)
        return "\n".join(l)


# --------------------------------------------------------------------------- formatos

def verificador_formatos():
    """Verificador de formatos sem dependências extras (date, date-time e uri)."""
    fc = FormatChecker(formats=())

    @fc.checks("date")
    def _data(v):  # noqa: ANN001
        if not isinstance(v, str):
            return True
        try:
            date.fromisoformat(v)
            return len(v) == 10
        except ValueError:
            return False

    @fc.checks("date-time")
    def _data_hora(v):  # noqa: ANN001
        return True if not isinstance(v, str) else data_hora_valida(v)

    @fc.checks("uri")
    def _uri(v):  # noqa: ANN001
        return True if not isinstance(v, str) else bool(re.match(r"^[A-Za-z][A-Za-z0-9+.\-]*:\S+$", v))

    return fc


def criar_validador_schema(contrato: Contrato):
    schema = gerar_schema(contrato)
    return Draft202012Validator(schema, format_checker=verificador_formatos()), schema


# --------------------------------------------------------------------------- leitura

class ErroUso(Exception):
    """Erro de uso (arquivo inexistente, extensão não suportada)."""


def _decodificar_json(nome: str, conteudo: bytes, rel: Relatorio) -> Any:
    if conteudo.startswith(b"\xef\xbb\xbf"):
        rel.observacoes.append(f"{nome}: o arquivo começa com BOM; prefira UTF-8 sem BOM")
        conteudo = conteudo[3:]
    try:
        texto = conteudo.decode("utf-8")
    except UnicodeDecodeError as e:
        rel.add("ARQ", f"{nome}: o arquivo não está em UTF-8 (byte inválido na posição {e.start})")
        return None
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        rel.add("ARQ", f"{nome}: JSON malformado na linha {e.lineno}, coluna {e.colno}: {e.msg}")
        return None


def ler_envio(caminho: Path, contrato: Contrato, rel: Relatorio) -> dict | None:
    """Lê o arquivo do envio (JSON, JSON.GZ, ZIP ou XLSX) e devolve o documento JSON."""
    from excel_para_json import ErroPlanilha, converter_excel

    if not caminho.is_file():
        raise ErroUso(f"arquivo não encontrado: {caminho}")
    nome = caminho.name.lower()
    if not nome.endswith((".json", ".json.gz", ".gz", ".zip", ".xlsx")):
        raise ErroUso(f"tipo de arquivo não suportado: {caminho.name} (use .json, .json.gz, .zip ou .xlsx)")
    bruto = caminho.read_bytes()
    rel.arquivos.append({"arquivo": caminho.name, "bytes": len(bruto),
                         "sha256": hashlib.sha256(bruto).hexdigest()})

    def de_excel(conteudo: bytes, rotulo: str) -> dict | None:
        try:
            doc, avisos, celulas = converter_excel(conteudo, contrato)
        except ErroPlanilha as e:
            rel.add("ARQ", f"{rotulo}: {e}")
            return None
        rel.avisos_conversao.extend(avisos)
        rel.celulas = celulas
        return doc

    if nome.endswith(".xlsx"):
        return de_excel(bruto, caminho.name)
    if nome.endswith(".gz"):
        try:
            conteudo = gzip.decompress(bruto)
        except (OSError, EOFError) as e:
            rel.add("ARQ", f"{caminho.name}: arquivo .gz corrompido ({e})")
            return None
        return _decodificar_json(caminho.name, conteudo, rel)
    if nome.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(bruto)) as z:
                membros = sorted(n for n in z.namelist() if not n.endswith("/"))
                jsons = [n for n in membros if n.lower().endswith(".json")]
                planilhas = [n for n in membros if n.lower().endswith(".xlsx")]
                if planilhas and not jsons and len(planilhas) == 1:
                    return de_excel(z.read(planilhas[0]), f"{caminho.name}!{planilhas[0]}")
                if not jsons:
                    rel.add("ARQ", f"{caminho.name}: o .zip não contém .json (nem uma única planilha .xlsx)")
                    return None
                partes = []
                for m in jsons:
                    d = _decodificar_json(f"{caminho.name}!{m}", z.read(m), rel)
                    if d is not None:
                        partes.append((m, d))
        except zipfile.BadZipFile as e:
            rel.add("ARQ", f"{caminho.name}: arquivo .zip corrompido ({e})")
            return None
        return _juntar_partes(partes, contrato, rel)
    return _decodificar_json(caminho.name, bruto, rel)


def _juntar_partes(partes: list[tuple[str, Any]], contrato: Contrato, rel: Relatorio) -> dict | None:
    if not partes:
        return None
    if len(partes) == 1:
        return partes[0][1]
    if not all(isinstance(d, dict) for _, d in partes):
        rel.add("ARQ", "todas as partes do .zip devem ser objetos JSON")
        return None
    base_nome, base = partes[0]
    junto: dict[str, Any] = {"envio": base.get("envio")}
    for nome, d in partes[1:]:
        if d.get("envio") != base.get("envio"):
            rel.add("ARQ", f"{nome}: cabeçalho 'envio' diferente do da parte {base_nome}; "
                           "todas as partes devem ter o mesmo cabeçalho")
    for b in contrato.nomes_blocos:
        lista: list = []
        for _, d in partes:
            v = d.get(b, [])
            if isinstance(v, list):
                lista.extend(v)
            else:
                junto[b] = v  # deixa o schema apontar o tipo errado
                break
        else:
            junto[b] = lista
    rel.observacoes.append(f"envio em {len(partes)} partes; regras aplicadas sobre a união das partes")
    return junto


# --------------------------------------------------------------------------- schema → R01/R05

def _erro_folha(erro):
    while erro.validator in ("anyOf", "oneOf") and erro.context:
        candidatos = [e for e in erro.context if not (e.validator == "type" and e.validator_value == "null")]
        erro = candidatos[0] if candidatos else erro.context[0]
    return erro


def _regra_do_erro(erro, schema: dict) -> tuple[str, str | None]:
    """Percorre o caminho do erro no schema; '$comment' iniciado por R05 marca obrigatoriedade condicional."""
    no: Any = schema
    regra, comentario = "R01", None
    for passo in erro.absolute_schema_path:
        if isinstance(no, dict) and "$ref" in no and passo not in no:
            ref = no["$ref"]
            no = schema["$defs"][ref.split("/")[-1]]
        try:
            no = no[passo]
        except (KeyError, IndexError, TypeError):
            break
        if isinstance(no, dict) and str(no.get("$comment", "")).startswith("R05"):
            regra, comentario = "R05", no["$comment"][5:].strip()
    return regra, comentario


def _mensagem(erro, comentario: str | None) -> str:
    v, val, inst = erro.validator, erro.validator_value, erro.instance
    if comentario and v in ("required", "not"):
        return comentario
    if v == "required":
        faltam = [c for c in val if isinstance(inst, dict) and c not in inst]
        return "campo obrigatório ausente: " + ", ".join(faltam)
    if v == "enum":
        return f"valor {json.dumps(inst, ensure_ascii=False)} fora do domínio; aceitos: {', '.join(map(str, val))}"
    if v == "const":
        return f"valor {json.dumps(inst, ensure_ascii=False)} inválido; deve ser {json.dumps(val, ensure_ascii=False)}"
    if v == "type":
        if inst is None:
            return "campo obrigatório com valor null"
        esperado = val if isinstance(val, list) else [val]
        return (f"tipo inválido ({json.dumps(inst, ensure_ascii=False, default=str)}); esperado "
                + " ou ".join(NOME_TIPO_JSON.get(t, t) for t in esperado))
    if v == "pattern":
        titulo = erro.schema.get("title") if isinstance(erro.schema, dict) else None
        return f"valor {json.dumps(inst, ensure_ascii=False)} fora do formato esperado" + (
            f" para {titulo}" if titulo else "")
    if v == "format":
        nomes = {"date": "data (AAAA-MM-DD)", "date-time": "data e hora com fuso", "uri": "URI"}
        return f"valor {json.dumps(inst, ensure_ascii=False)} não é {nomes.get(val, val)} válida"
    if v == "minLength":
        return "texto vazio; preencha ou omita o campo"
    if v == "maxLength":
        return f"texto com {len(inst)} caracteres; máximo {val}"
    if v == "minimum":
        return f"valor {inst} menor que o mínimo {val}"
    if v == "maximum":
        return f"valor {inst} maior que o máximo {val}"
    if v == "additionalProperties":
        extras = [k for k in inst if k not in erro.schema.get("properties", {})] if isinstance(inst, dict) else []
        return "campo não previsto no layout: " + ", ".join(extras)
    if v == "not":
        return "campo obrigatório nesta condição"
    return erro.message


def _rotulo_chave(contrato: Contrato, bloco: str, reg: Any) -> str | None:
    b = contrato.bloco(bloco)
    if not b or not isinstance(reg, dict):
        return None
    campos = b.chave or b.nomes[:1]
    partes = [f"{k}={reg.get(k)}" for k in campos if reg.get(k) not in (None, "")]
    return ", ".join(partes) or None


def aplicar_schema(doc: Any, validador, schema: dict, contrato: Contrato, rel: Relatorio) -> None:
    for erro in validador.iter_errors(doc):
        folha = _erro_folha(erro)
        regra, comentario = _regra_do_erro(folha, schema)
        if regra == "R01":
            regra, comentario = _regra_do_erro(erro, schema)
        caminho = list(folha.absolute_path)
        bloco = chave = campo = indice = None
        if caminho and caminho[0] in contrato.nomes_blocos:
            bloco = caminho[0]
            if len(caminho) > 1 and isinstance(caminho[1], int):
                indice = caminho[1]
                try:
                    chave = _rotulo_chave(contrato, bloco, doc[bloco][indice]) or f"registro {indice + 1}"
                except (KeyError, IndexError, TypeError):
                    chave = f"registro {indice + 1}"
                resto = caminho[2:]
            else:
                resto = caminho[1:]
            campo = ".".join(map(str, resto)) or None
        elif caminho and caminho[0] == "envio":
            bloco = "envio"
            campo = ".".join(map(str, caminho[1:])) or None
        else:
            campo = ".".join(map(str, caminho)) or None
        if folha.validator == "required" and isinstance(folha.instance, dict):
            faltam = [c for c in folha.validator_value if c not in folha.instance]
            if len(faltam) == 1:
                campo = (campo + "." if campo else "") + faltam[0]
        elif folha.validator == "additionalProperties" and isinstance(folha.instance, dict):
            pass
        rel.add(regra, _mensagem(folha, comentario), bloco, chave, campo, indice)


# --------------------------------------------------------------------------- regras automáticas

def _registros(doc: dict, bloco: str) -> list[tuple[int, dict]]:
    v = doc.get(bloco)
    return [(i, r) for i, r in enumerate(v) if isinstance(r, dict)] if isinstance(v, list) else []


def aplicar_regras_automaticas(contrato: Contrato, doc: dict, rel: Relatorio) -> None:
    envio = doc.get("envio") if isinstance(doc.get("envio"), dict) else {}
    data_ref = para_data(envio.get("data_referencia")) if isinstance(envio.get("data_referencia"), str) else None
    completa = envio.get("tipo_carga") == "COMPLETA"

    # R02 — chave única
    for b in contrato.blocos:
        if not b.chave:
            continue
        cont: Counter = Counter()
        primeiros: dict = {}
        for i, r in _registros(doc, b.nome):
            k = tuple(r.get(c) for c in b.chave)
            if any(v is None or isinstance(v, (dict, list)) for v in k):
                continue
            cont[k] += 1
            primeiros.setdefault(k, i)
        for k, n in cont.items():
            if n > 1:
                rotulo = ", ".join(f"{c}={v}" for c, v in zip(b.chave, k))
                rel.add("R02", f"a chave aparece {n} vezes no bloco; deve ser única",
                        b.nome, rotulo, None, primeiros[k])

    # R03 — referências (só na carga COMPLETA)
    tem_ref = any(c.referencia for b in contrato.blocos for c in b.campos)
    if tem_ref and not completa:
        rel.observacoes.append("carga INCREMENTAL: R03 (referências) depende do histórico acumulado "
                               "e não é aplicada a este arquivo isolado")
    if completa:
        for b in contrato.blocos:
            for c in b.campos:
                if not c.referencia:
                    continue
                alvo_bloco, alvo_campo = c.referencia.split(".", 1)
                existentes = {r.get(alvo_campo) for _, r in _registros(doc, alvo_bloco)}
                for i, r in _registros(doc, b.nome):
                    v = r.get(c.nome)
                    if v is None or isinstance(v, (dict, list)):
                        continue
                    if v not in existentes:
                        rel.add("R03", f"{c.nome} = {v} não existe em {c.referencia}",
                                b.nome, _rotulo_chave(contrato, b.nome, r), c.nome, i)

    # R04 — datas de evento ≤ data_referencia; data_referencia_anterior < data_referencia
    anterior = envio.get("data_referencia_anterior")
    d_ant = para_data(anterior) if isinstance(anterior, str) else None
    if data_ref and d_ant and d_ant >= data_ref:
        rel.add("R04", f"data_referencia_anterior = {anterior} deve ser anterior à data_referencia "
                       f"{data_ref.isoformat()}", "envio", None, "data_referencia_anterior", None)
    if data_ref:
        locais = [("envio", contrato.cabecalho, [(None, envio)])]
        locais += [(b.nome, b.campos, _registros(doc, b.nome)) for b in contrato.blocos]
        for bloco, campos, registros in locais:
            eventos = [c for c in campos if c.evento]
            for i, r in registros:
                for c in eventos:
                    d = para_data(r.get(c.nome)) if isinstance(r.get(c.nome), str) else None
                    if d and d > data_ref:
                        chave = None if bloco == "envio" else _rotulo_chave(contrato, bloco, r)
                        rel.add("R04", f"{c.nome} = {r.get(c.nome)} é posterior à data_referencia "
                                       f"{data_ref.isoformat()}", bloco, chave, c.nome, i)

    # R07 — dígito verificador
    locais = [("envio", contrato.cabecalho, [(None, envio)])]
    locais += [(b.nome, b.campos, _registros(doc, b.nome)) for b in contrato.blocos]
    padrao = {"cnpj": r"^[0-9]{14}$", "cpf": r"^[0-9]{11}$", "cpf_cnpj": r"^([0-9]{11}|[0-9]{14})$"}
    for bloco, campos, registros in locais:
        docs = [c for c in campos if c.tipo in TIPOS_DOCUMENTO]
        for i, r in registros:
            for c in docs:
                v = r.get(c.nome)
                if isinstance(v, str) and re.match(padrao[c.tipo], v) and not documento_valido(c.tipo, v):
                    tipo = "CNPJ" if len(v) == 14 else "CPF"
                    chave = None if bloco == "envio" else _rotulo_chave(contrato, bloco, r)
                    rel.add("R07", f"{c.nome} = {v}: {tipo} com dígito verificador inválido",
                            bloco, chave, c.nome, i)

    # R08 — totais
    totais = envio.get("totais") if isinstance(envio.get("totais"), dict) else {}
    for b in contrato.blocos:
        informado = totais.get(b.nome)
        real = len(doc.get(b.nome)) if isinstance(doc.get(b.nome), list) else None
        if isinstance(informado, int) and not isinstance(informado, bool) and real is not None and informado != real:
            rel.add("R08", f"totais.{b.nome} informa {informado}, mas o envio contém {real} registro(s)",
                    "envio", None, f"totais.{b.nome}", None)


# --------------------------------------------------------------------------- regras do contrato

def aplicar_regras_contrato(contrato: Contrato, doc: dict, rel: Relatorio) -> None:
    envio = doc.get("envio") if isinstance(doc.get("envio"), dict) else {}
    contexto = {k: ([Registro(r) for r in v if isinstance(r, dict)] if isinstance(v, list) else v)
                for k, v in doc.items()}
    if isinstance(contexto.get("envio"), dict):
        contexto["envio"] = Registro(contexto["envio"])
    contexto = Registro(contexto)

    for regra in contrato.regras:
        if regra.bloco == "envio":
            registros = [(None, envio)]
        else:
            registros = _registros(doc, regra.bloco)
        for i, r in registros:
            chave = None if regra.bloco == "envio" else _rotulo_chave(contrato, regra.bloco, r)
            if regra.tipo == "ordem_datas":
                va, vd = r.get(regra.antes), r.get(regra.depois)
                da = _instante(va)
                dd = _instante(vd)
                if da is not None and dd is not None and dd < da:
                    rel.add(regra.id, f"{regra.mensagem} ({regra.antes} = {va}, {regra.depois} = {vd})",
                            regra.bloco, chave, regra.depois, i)
            elif regra.tipo == "data_minima":
                v = r.get(regra.campo)
                d = para_data(v) if isinstance(v, str) else None
                if d and d < date.fromisoformat(regra.valor):
                    rel.add(regra.id, f"{regra.mensagem} ({regra.campo} = {v}, mínimo {regra.valor})",
                            regra.bloco, chave, regra.campo, i)
            elif regra.tipo == "condicional":
                if regra.se.avaliar(r) and not regra.entao.avaliar(r):
                    rel.add(regra.id, f"{regra.mensagem} (se {regra.se.texto()}, então {regra.entao.texto()}; "
                                      f"{regra.entao.campo} = {r.get(regra.entao.campo)})",
                            regra.bloco, chave, regra.entao.campo, i)
            elif regra.tipo == "expressao":
                try:
                    ok = avaliar_expressao(regra.codigo, Registro(r), contexto)
                except Exception as e:  # a expressão é do contrato; o erro é reportado na própria regra
                    rel.add(regra.id, f"não foi possível avaliar a condição ({type(e).__name__}: {e})",
                            regra.bloco, chave, None, i)
                    continue
                if not ok:
                    rel.add(regra.id, regra.mensagem, regra.bloco, chave, None, i)


def _instante(v: Any):
    """Converte data ou data_hora em valor comparável (datetime com fuso ou date)."""
    if not isinstance(v, str):
        return None
    if len(v) == 10:
        d = para_data(v)
        return datetime(d.year, d.month, d.day) if d else None
    if data_hora_valida(v):
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None) - (dt.utcoffset() or timedelta())
    return None


# --------------------------------------------------------------------------- principal

def validar_documento(contrato: Contrato, doc: Any, rel: Relatorio | None = None) -> Relatorio:
    """Valida um documento JSON já carregado (dict) e devolve o relatório."""
    rel = rel or Relatorio(contrato)
    validador, schema = criar_validador_schema(contrato)
    aplicar_schema(doc, validador, schema, contrato, rel)
    if not isinstance(doc, dict):
        return rel
    envio = doc.get("envio") if isinstance(doc.get("envio"), dict) else {}
    rel.resumo = {
        "remetente": envio.get("remetente"),
        "data_referencia": envio.get("data_referencia"),
        "tipo_carga": envio.get("tipo_carga"),
        "contagem": {b: (len(doc[b]) if isinstance(doc.get(b), list) else 0) for b in contrato.nomes_blocos},
    }
    aplicar_regras_automaticas(contrato, doc, rel)
    aplicar_regras_contrato(contrato, doc, rel)
    return rel


def validar_arquivo(contrato: Contrato, caminho: Path, max_mensagens: int = 50) -> tuple[Relatorio, Any]:
    """Lê e valida o arquivo do envio. Devolve (relatório, documento JSON ou None)."""
    rel = Relatorio(contrato, max_mensagens)
    doc = ler_envio(Path(caminho), contrato, rel)
    if doc is None:
        if not rel.contagem("ARQ"):
            rel.add("ARQ", "nenhum conteúdo encontrado no arquivo")
        return rel, None
    validar_documento(contrato, doc, rel)
    return rel, doc


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:  # pragma: no cover
            pass
    ap = argparse.ArgumentParser(
        description="Valida um envio (JSON ou Excel) contra o contrato de coleta.",
        epilog="Saída: 0 = aceito; 1 = rejeitado; 2 = erro de uso.")
    ap.add_argument("contrato", type=Path, help="caminho do contrato.yaml")
    ap.add_argument("envio", type=Path, help="arquivo do envio: .json, .json.gz, .zip ou .xlsx")
    ap.add_argument("--json", action="store_true", help="imprime o relatório em JSON")
    ap.add_argument("--saida", type=Path, help="grava o relatório também neste arquivo")
    ap.add_argument("--exportar-json", type=Path, metavar="ARQUIVO",
                    help="grava o JSON convertido (útil para planilhas)")
    ap.add_argument("--max-mensagens", type=int, default=50, help="máximo de ocorrências exibidas por regra")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 2

    if Draft202012Validator is None:  # pragma: no cover
        print("ERRO: a biblioteca jsonschema não está instalada (pip install --user jsonschema)", file=sys.stderr)
        return 2
    try:
        contrato = carregar_contrato(args.contrato)
    except ErroContrato as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    try:
        rel, doc = validar_arquivo(contrato, args.envio, args.max_mensagens)
    except ErroUso as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2

    saida = json.dumps(rel.como_dict(), ensure_ascii=False, indent=2) if args.json else rel.como_texto()
    print(saida)
    if args.saida:
        args.saida.write_text(saida + "\n", encoding="utf-8")
    if args.exportar_json and doc is not None:
        args.exportar_json.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.json:
            print(f"JSON convertido gravado em {args.exportar_json}")
    return 1 if rel.rejeitado else 0


if __name__ == "__main__":
    sys.exit(main())
