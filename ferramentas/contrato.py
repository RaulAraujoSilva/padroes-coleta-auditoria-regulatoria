# -*- coding: utf-8 -*-
"""
Carrega e valida o contrato de coleta (`contrato.yaml`).

O contrato é a fonte única de verdade: a partir dele as demais ferramentas geram o
JSON Schema, o modelo Excel, a especificação OpenAPI, o dicionário de dados e o
envio de exemplo, e o validador confere os envios recebidos.

Uso como biblioteca:

    from contrato import carregar_contrato, ErroContrato
    try:
        c = carregar_contrato("contrato.yaml")
    except ErroContrato as erro:
        print(erro)            # lista legível de todos os problemas encontrados
    for aviso in c.avisos:     # pontos que não impedem o uso, mas merecem atenção
        print(aviso)

Uso pela linha de comando (só confere o contrato):

    python ferramentas/contrato.py caminho/contrato.yaml

Especificação do formato: docs/formato-contrato.md.
"""
from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

# --------------------------------------------------------------------------- constantes

TIPOS = (
    "texto", "inteiro", "decimal", "data", "data_hora", "booleano", "enum",
    "cnpj", "cpf", "cpf_cnpj", "cep", "ibge_municipio", "url", "sha256",
)
TIPOS_NUMERICOS = ("inteiro", "decimal")
TIPOS_DATA = ("data", "data_hora")
TIPOS_DOCUMENTO = ("cnpj", "cpf", "cpf_cnpj")
TIPOS_TEXTUAIS = ("texto", "enum", "cnpj", "cpf", "cpf_cnpj", "cep", "ibge_municipio", "url", "sha256")

# Expressões regulares de formato por tipo (usadas no schema, no Excel e no validador).
PADRAO_TIPO = {
    "data": r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$",
    "data_hora": (r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])"
                  r"T([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9](\.[0-9]+)?)?(Z|[+-]([01][0-9]|2[0-3]):[0-5][0-9])$"),
    "cnpj": r"^[0-9]{14}$",
    "cpf": r"^[0-9]{11}$",
    "cpf_cnpj": r"^([0-9]{11}|[0-9]{14})$",
    "cep": r"^[0-9]{8}$",
    "ibge_municipio": r"^[0-9]{7}$",
    "url": r"^[A-Za-z][A-Za-z0-9+.\-]*://[^\s]+$",
    "sha256": r"^[0-9a-fA-F]{64}$",
}

DESCRICAO_FORMATO_TIPO = {
    "texto": "texto",
    "inteiro": "número inteiro",
    "decimal": "número (ponto como separador decimal no JSON)",
    "data": "data AAAA-MM-DD",
    "data_hora": "data e hora ISO 8601 com fuso, AAAA-MM-DDThh:mm:ss-03:00",
    "booleano": "true/false (no Excel: SIM/NAO)",
    "enum": "um dos valores do domínio",
    "cnpj": "CNPJ com 14 dígitos, só números",
    "cpf": "CPF com 11 dígitos, só números",
    "cpf_cnpj": "CPF (11 dígitos) ou CNPJ (14 dígitos), só números",
    "cep": "CEP com 8 dígitos, só números",
    "ibge_municipio": "código IBGE do município, 7 dígitos",
    "url": "endereço URI, ex.: https://...",
    "sha256": "hash SHA-256, 64 caracteres hexadecimais",
}

CLASSIFICACOES = ("computavel", "parcialmente_computavel", "discricionaria")
PERIODICIDADES = ("diaria", "semanal", "mensal", "trimestral", "anual", "sob_demanda")
TIPOS_REGRA = ("ordem_datas", "data_minima", "condicional", "expressao")
SEVERIDADES = ("rejeicao", "alerta")
OPERADORES_CONDICAO = ("igual", "diferente", "em", "preenchido")

# Regras automáticas (docs/formato-contrato.md, seção "Regras automáticas").
REGRAS_AUTOMATICAS = {
    "R01": "Obrigatórios presentes; tipo, formato e domínio corretos",
    "R02": "Chave única dentro do bloco",
    "R03": "Referência existe no bloco referenciado (só na carga COMPLETA)",
    "R04": "Datas de evento não posteriores à data_referencia (e data_referencia_anterior anterior a ela)",
    "R05": "Obrigatoriedade condicional",
    "R07": "Dígito verificador de CNPJ e CPF",
    "R08": "Totais do cabeçalho iguais à contagem real",
}
IDS_RESERVADOS = set(REGRAS_AUTOMATICAS)
RE_ID_REGRA = re.compile(r"^(R|A)[0-9]{2,}$")

RE_NOME_CONTRATO = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RE_SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
RE_VERSAO = re.compile(r"^[0-9]+\.[0-9]+$")

NOMES_RESERVADOS_BLOCO = {"envio", "totais"}

BUILTINS_EXPRESSAO = {
    "any": any, "all": all, "len": len, "min": min, "max": max, "sum": sum,
    "set": set, "str": str, "int": int, "float": float,
    "bool": bool,  # acréscimo conservador à lista da especificação (ver ferramentas/README.md)
}

CHAVES_TOPO = {
    "contrato", "versao", "titulo", "descricao", "orgao", "regulados", "base_normativa",
    "teste_auditoria", "periodicidade", "cabecalho", "blocos", "regras",
}
CHAVES_CAMPO = {
    "nome", "tipo", "obrigatorio", "descricao", "origem", "exemplo", "tamanho_max",
    "formato", "dominio", "referencia", "evento", "minimo", "maximo",
}
CHAVES_BLOCO = {"nome", "descricao", "chave", "campos"}
CHAVES_REGRA = {
    "id", "tipo", "severidade", "bloco", "mensagem", "descricao",
    "antes", "depois", "campo", "valor", "se", "entao", "condicao",
}


class ErroContrato(Exception):
    """Contrato inválido. `erros` traz a lista completa de problemas encontrados."""

    def __init__(self, erros: list[str], caminho: str | None = None):
        self.erros = erros
        self.caminho = caminho
        cab = f"Contrato inválido ({caminho})" if caminho else "Contrato inválido"
        super().__init__(cab + f": {len(erros)} problema(s)\n" + "\n".join(f"  - {e}" for e in erros))


# --------------------------------------------------------------------------- documentos (CNPJ/CPF)

def cnpj_valido(doc: Any) -> bool:
    """Confere os dígitos verificadores de um CNPJ numérico de 14 dígitos."""
    if not isinstance(doc, str) or len(doc) != 14 or not doc.isdigit() or doc == doc[0] * 14:
        return False

    def dv(base: str, pesos: list[int]) -> str:
        r = sum(int(a) * b for a, b in zip(base, pesos)) % 11
        return "0" if r < 2 else str(11 - r)

    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = dv(doc[:12], p1)
    d2 = dv(doc[:12] + d1, [6] + p1)
    return doc[12:] == d1 + d2


def cpf_valido(doc: Any) -> bool:
    """Confere os dígitos verificadores de um CPF de 11 dígitos."""
    if not isinstance(doc, str) or len(doc) != 11 or not doc.isdigit() or doc == doc[0] * 11:
        return False

    def dv(base: str) -> str:
        n = len(base) + 1
        r = sum(int(a) * (n - i) for i, a in enumerate(base)) % 11
        return "0" if r < 2 else str(11 - r)

    d1 = dv(doc[:9])
    d2 = dv(doc[:9] + d1)
    return doc[9:] == d1 + d2


def documento_valido(tipo: str, doc: Any) -> bool:
    if tipo == "cnpj":
        return cnpj_valido(doc)
    if tipo == "cpf":
        return cpf_valido(doc)
    if isinstance(doc, str) and len(doc) == 14:
        return cnpj_valido(doc)
    return cpf_valido(doc)


def completar_cnpj(base12: str) -> str:
    """Acrescenta os dois dígitos verificadores a uma base de 12 dígitos."""
    def dv(base: str, pesos: list[int]) -> str:
        r = sum(int(a) * b for a, b in zip(base, pesos)) % 11
        return "0" if r < 2 else str(11 - r)

    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = dv(base12, p1)
    return base12 + d1 + dv(base12 + d1, [6] + p1)


def completar_cpf(base9: str) -> str:
    """Acrescenta os dois dígitos verificadores a uma base de 9 dígitos."""
    def dv(base: str) -> str:
        n = len(base) + 1
        r = sum(int(a) * (n - i) for i, a in enumerate(base)) % 11
        return "0" if r < 2 else str(11 - r)

    d1 = dv(base9)
    return base9 + d1 + dv(base9 + d1)


# --------------------------------------------------------------------------- datas

def para_data(valor: Any) -> date | None:
    """Converte 'AAAA-MM-DD' ou 'AAAA-MM-DDThh:mm...' na data correspondente (ou None)."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str):
        return None
    try:
        if len(valor) == 10:
            return date.fromisoformat(valor)
        if re.match(PADRAO_TIPO["data_hora"], valor):
            return datetime.fromisoformat(valor.replace("Z", "+00:00")).date()
    except ValueError:
        return None
    return None


def data_hora_valida(valor: Any) -> bool:
    if not isinstance(valor, str) or not re.match(PADRAO_TIPO["data_hora"], valor):
        return False
    try:
        datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


# --------------------------------------------------------------------------- modelo de dados

@dataclass
class Condicao:
    """Condição sobre um campo do mesmo registro: igual, diferente, em ou preenchido."""
    campo: str
    operador: str
    valor: Any

    def avaliar(self, registro: dict) -> bool:
        v = registro.get(self.campo) if isinstance(registro, dict) else None
        presente = v is not None and v != ""
        if self.operador == "preenchido":
            return presente if self.valor else not presente
        if not presente:
            return False
        if self.operador == "igual":
            return v == self.valor
        if self.operador == "diferente":
            return v != self.valor
        if self.operador == "em":
            return v in self.valor
        return False  # pragma: no cover

    def texto(self) -> str:
        if self.operador == "preenchido":
            return f"{self.campo} preenchido" if self.valor else f"{self.campo} não preenchido"
        if self.operador == "igual":
            return f"{self.campo} = {_fmt(self.valor)}"
        if self.operador == "diferente":
            return f"{self.campo} ≠ {_fmt(self.valor)} (e preenchido)"
        return f"{self.campo} em [{', '.join(_fmt(v) for v in self.valor)}]"


def _fmt(v: Any) -> str:
    if isinstance(v, bool):
        return "SIM" if v else "NAO"
    return str(v)


@dataclass
class Campo:
    nome: str
    tipo: str
    obrigatorio: bool | Condicao = False
    descricao: str = ""
    origem: str = ""
    exemplo: Any = None
    tamanho_max: int | None = None
    formato: str | None = None
    dominio: list[str] | None = None
    referencia: str | None = None
    evento: bool = False
    minimo: float | int | None = None
    maximo: float | int | None = None
    constante: Any = None          # só nos campos automáticos `contrato` e `versao_layout`
    automatico: bool = False       # campo do cabeçalho automático

    @property
    def sempre_obrigatorio(self) -> bool:
        return self.obrigatorio is True

    @property
    def condicional(self) -> bool:
        return isinstance(self.obrigatorio, Condicao)

    @property
    def bloco_referenciado(self) -> str | None:
        return self.referencia.split(".", 1)[0] if self.referencia else None

    @property
    def campo_referenciado(self) -> str | None:
        return self.referencia.split(".", 1)[1] if self.referencia else None

    def texto_obrigatorio(self) -> str:
        if self.obrigatorio is True:
            return "Sim"
        if self.obrigatorio is False:
            return "Não"
        return f"Se {self.obrigatorio.texto()}"

    def texto_dominio(self) -> str:
        """Descrição curta de domínio/formato, usada no Excel, no dicionário e na OpenAPI."""
        partes: list[str] = []
        if self.constante is not None:
            partes.append(f"igual a {self.constante}")
        if self.dominio:
            partes.append(", ".join(self.dominio))
        else:
            partes.append(DESCRICAO_FORMATO_TIPO[self.tipo])
        if self.formato:
            partes.append(f"formato {self.formato}")
        if self.tamanho_max:
            partes.append(f"até {self.tamanho_max} caracteres")
        if self.minimo is not None:
            partes.append(f"mínimo {self.minimo}")
        if self.maximo is not None:
            partes.append(f"máximo {self.maximo}")
        if self.referencia:
            partes.append(f"deve existir em {self.referencia}")
        if self.evento:
            partes.append("não pode ser posterior à data_referencia")
        return "; ".join(partes)


@dataclass
class Bloco:
    nome: str
    descricao: str
    chave: list[str]
    campos: list[Campo]

    def campo(self, nome: str) -> Campo | None:
        for c in self.campos:
            if c.nome == nome:
                return c
        return None

    @property
    def nomes(self) -> list[str]:
        return [c.nome for c in self.campos]


@dataclass
class Regra:
    id: str
    tipo: str
    severidade: str
    mensagem: str
    bloco: str = "envio"           # "envio" = cabeçalho
    antes: str | None = None
    depois: str | None = None
    campo: str | None = None
    valor: Any = None
    se: Condicao | None = None
    entao: Condicao | None = None
    condicao: str | None = None
    codigo: Any = None             # expressão compilada (tipo expressao)

    @property
    def descricao(self) -> str:
        return self.mensagem


@dataclass
class Lacuna:
    id: str
    trecho: str = ""
    problema: str = ""
    decisao_padrao: str = ""
    quem_decide: str = ""


@dataclass
class Contrato:
    contrato: str
    versao: str
    titulo: str
    descricao: str
    orgao: str
    regulados: list[str]
    base_normativa: list[dict]
    teste_auditoria: dict
    lacunas: list[Lacuna]
    periodicidade: dict
    cabecalho: list[Campo]           # automáticos + definidos no contrato
    blocos: list[Bloco]
    regras: list[Regra]
    caminho: str | None = None
    avisos: list[str] = field(default_factory=list)

    def bloco(self, nome: str) -> Bloco | None:
        for b in self.blocos:
            if b.nome == nome:
                return b
        return None

    def campos_de(self, bloco: str) -> list[Campo]:
        if bloco == "envio":
            return self.cabecalho
        b = self.bloco(bloco)
        return b.campos if b else []

    def campo_de(self, bloco: str, nome: str) -> Campo | None:
        for c in self.campos_de(bloco):
            if c.nome == nome:
                return c
        return None

    @property
    def nomes_blocos(self) -> list[str]:
        return [b.nome for b in self.blocos]

    @property
    def cabecalho_automatico(self) -> list[Campo]:
        return [c for c in self.cabecalho if c.automatico]

    @property
    def cabecalho_contrato(self) -> list[Campo]:
        return [c for c in self.cabecalho if not c.automatico]

    @property
    def versao_maior(self) -> str:
        return self.versao.split(".")[0]

    @property
    def nome_base(self) -> str:
        """Prefixo dos artefatos: <contrato>-<versao>."""
        return f"{self.contrato}-{self.versao}"

    def catalogo_regras(self) -> list[tuple[str, str, str]]:
        """(id, descrição, severidade) de todas as regras, automáticas e do contrato."""
        itens = [(rid, desc, "rejeicao") for rid, desc in REGRAS_AUTOMATICAS.items()]
        itens += [(r.id, r.mensagem, r.severidade) for r in self.regras]
        return itens


# --------------------------------------------------------------------------- cabeçalho automático

NOMES_CABECALHO_AUTOMATICO = (
    "contrato", "versao_layout", "remetente", "cnpj_remetente", "data_referencia",
    "tipo_carga", "data_referencia_anterior", "gerado_em",
)


def _cabecalho_automatico(contrato: str, versao: str, regulados: list[str]) -> list[Campo]:
    return [
        Campo("contrato", "texto", True, "Identificador do contrato de coleta.",
              "gerado pela ferramenta", contrato, constante=contrato, automatico=True),
        Campo("versao_layout", "texto", True, "Versão do layout de dados usada no envio.",
              "gerado pela ferramenta", versao, constante=versao, automatico=True),
        Campo("remetente", "enum", True, "Regulado que envia os dados.",
              "regulado", regulados[0] if regulados else None, dominio=list(regulados), automatico=True),
        Campo("cnpj_remetente", "cnpj", True, "CNPJ de quem envia, 14 dígitos sem pontuação.",
              "regulado", completar_cnpj("112223330001"), automatico=True),
        Campo("data_referencia", "data", True,
              "Data de corte: o envio reflete a posição dos dados até este dia, inclusive.",
              "regulado", None, automatico=True),
        Campo("tipo_carga", "enum", True,
              "COMPLETA (todo o universo e histórico) ou INCREMENTAL (só o que mudou desde o envio anterior).",
              "regulado", "COMPLETA", dominio=["COMPLETA", "INCREMENTAL"], automatico=True),
        Campo("data_referencia_anterior", "data", Condicao("tipo_carga", "igual", "INCREMENTAL"),
              "Data de referência do envio anterior; obrigatória na carga INCREMENTAL.",
              "regulado", None, automatico=True),
        Campo("gerado_em", "data_hora", True, "Momento em que o arquivo foi gerado, com fuso horário.",
              "gerado pela ferramenta do regulado", None, automatico=True),
    ]


# --------------------------------------------------------------------------- expressão restrita

_NOS_PERMITIDOS = (
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare, ast.IfExp, ast.Call,
    ast.Name, ast.Load, ast.Store, ast.Constant, ast.Attribute, ast.Subscript, ast.Slice,
    ast.List, ast.Tuple, ast.Set, ast.Dict, ast.ListComp, ast.SetComp, ast.DictComp,
    ast.GeneratorExp, ast.comprehension, ast.keyword,
    ast.And, ast.Or, ast.Not, ast.Invert, ast.UAdd, ast.USub,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn, ast.Is, ast.IsNot,
)


def compilar_expressao(texto: str):
    """Compila a condição de uma regra `expressao`, recusando construções inseguras.

    Permitido: comparações, operadores lógicos e aritméticos, compreensões, indexação,
    métodos de dicionário/lista/texto (ex.: `r.get('x')`) e as funções
    any, all, len, min, max, sum, set, str, int, float. Proibido: lambda, atribuição,
    importação e qualquer nome ou atributo iniciado por sublinhado.
    """
    try:
        arvore = ast.parse(texto, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"sintaxe inválida na condição ({e.msg}, coluna {e.offset})") from None
    for no in ast.walk(arvore):
        if not isinstance(no, _NOS_PERMITIDOS):
            raise ValueError(f"construção não permitida na condição: {type(no).__name__}")
        if isinstance(no, ast.Name) and no.id.startswith("_"):
            raise ValueError(f"nome não permitido na condição: {no.id}")
        if isinstance(no, ast.Attribute) and no.attr.startswith("_"):
            raise ValueError(f"atributo não permitido na condição: {no.attr}")
    # nomes lidos devem ser r, e, uma função permitida ou variável de compreensão
    locais = {n.id for n in ast.walk(arvore) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    permitidos = {"r", "e"} | set(BUILTINS_EXPRESSAO) | locais
    for no in ast.walk(arvore):
        if isinstance(no, ast.Name) and isinstance(no.ctx, ast.Load) and no.id not in permitidos:
            raise ValueError(f"nome desconhecido na condição: {no.id} (use r, e ou "
                             f"{', '.join(BUILTINS_EXPRESSAO)})")
    return compile(arvore, "<regra>", "eval")


class Registro(dict):
    """Dicionário de registro em que um campo ausente vale None (para as expressões)."""

    def __missing__(self, chave):
        return None


def avaliar_expressao(codigo, registro: dict, envio: dict) -> bool:
    """Avalia a expressão com builtins restritos e as variáveis `r` (registro) e `e` (envio)."""
    # r e e ficam nos GLOBAIS: o escopo de geradores e compreensões não enxerga os locais do eval.
    ambiente = {"__builtins__": BUILTINS_EXPRESSAO, "r": registro, "e": envio}
    return bool(eval(codigo, ambiente))  # noqa: S307 (eval restrito)


# --------------------------------------------------------------------------- carga e validação

class _Coletor:
    def __init__(self):
        self.erros: list[str] = []
        self.avisos: list[str] = []

    def erro(self, msg: str) -> None:
        self.erros.append(msg)

    def aviso(self, msg: str) -> None:
        self.avisos.append(msg)


def _texto_opcional(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _chaves_desconhecidas(obj: dict, permitidas: set[str], onde: str, col: _Coletor) -> None:
    extras = sorted(k for k in obj if k not in permitidas)
    if extras:
        col.aviso(f"{onde}: chave(s) desconhecida(s) ignorada(s): {', '.join(map(str, extras))}")


def _ler_condicao(obj: Any, onde: str, col: _Coletor, campo_chave: str = "se") -> Condicao | None:
    """Lê {se: campo, igual: X} (obrigatoriedade) ou {campo: c, igual: X} (regra condicional)."""
    if not isinstance(obj, dict):
        col.erro(f"{onde}: a condição deve ser um objeto com '{campo_chave}' e um operador "
                 f"({', '.join(OPERADORES_CONDICAO)})")
        return None
    alvo = obj.get(campo_chave)
    if not isinstance(alvo, str) or not alvo:
        col.erro(f"{onde}: falta '{campo_chave}' (nome do campo da condição)")
        return None
    ops = [k for k in OPERADORES_CONDICAO if k in obj]
    extras = [k for k in obj if k not in OPERADORES_CONDICAO and k != campo_chave]
    if extras:
        col.erro(f"{onde}: chave(s) não reconhecida(s) na condição: {', '.join(map(str, extras))}")
    if len(ops) != 1:
        col.erro(f"{onde}: a condição deve ter exatamente um operador entre "
                 f"{', '.join(OPERADORES_CONDICAO)} (encontrado(s): {', '.join(ops) or 'nenhum'})")
        return None
    op = ops[0]
    valor = obj[op]
    if op == "em" and (not isinstance(valor, list) or not valor):
        col.erro(f"{onde}: o operador 'em' exige uma lista não vazia de valores")
        return None
    if op == "preenchido" and not isinstance(valor, bool):
        col.erro(f"{onde}: o operador 'preenchido' aceita só true ou false")
        return None
    if op in ("igual", "diferente") and (valor is None or isinstance(valor, (list, dict))):
        col.erro(f"{onde}: o operador '{op}' exige um único valor")
        return None
    return Condicao(alvo, op, valor)


def _conferir_valor_condicao(cond: Condicao, campo_alvo: Campo, onde: str, col: _Coletor) -> None:
    if cond.operador == "preenchido":
        return
    valores = cond.valor if cond.operador == "em" else [cond.valor]
    for v in valores:
        if campo_alvo.tipo == "enum" and campo_alvo.dominio and v not in campo_alvo.dominio:
            col.erro(f"{onde}: o valor {v!r} não pertence ao domínio de {campo_alvo.nome} "
                     f"({', '.join(campo_alvo.dominio)})")
        elif campo_alvo.tipo == "booleano" and not isinstance(v, bool):
            col.erro(f"{onde}: {campo_alvo.nome} é booleano; use true ou false na condição")
        elif campo_alvo.tipo in TIPOS_NUMERICOS and (isinstance(v, bool) or not isinstance(v, (int, float))):
            col.erro(f"{onde}: {campo_alvo.nome} é numérico; use um número na condição")


def _normalizar_exemplo(c: Campo) -> Any:
    """Converte o `exemplo` do YAML no valor JSON correspondente ao tipo."""
    v = c.exemplo
    if v is None:
        return None
    if c.tipo == "data" and isinstance(v, (date, datetime)):
        return (v.date() if isinstance(v, datetime) else v).isoformat()
    if c.tipo == "data_hora" and isinstance(v, datetime):
        return v.isoformat()
    if c.tipo == "booleano" and isinstance(v, str):
        if v.strip().upper() in ("SIM", "TRUE"):
            return True
        if v.strip().upper() in ("NAO", "NÃO", "FALSE"):
            return False
    if c.tipo in TIPOS_TEXTUAIS and isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    if c.tipo == "decimal" and isinstance(v, int) and not isinstance(v, bool):
        return v
    return v


def problema_valor(c: Campo, v: Any) -> str | None:
    """Confere um valor (já em forma JSON) contra o tipo e as restrições do campo.

    Devolve None quando o valor é válido, ou a descrição do problema. Usado para
    conferir os `exemplo` do contrato; o envio é conferido pelo JSON Schema.
    """
    t = c.tipo
    if t in TIPOS_TEXTUAIS or t in TIPOS_DATA:
        if not isinstance(v, str):
            return f"deve ser texto ({DESCRICAO_FORMATO_TIPO[t]})"
        if t == "data":
            if not re.match(PADRAO_TIPO["data"], v) or para_data(v) is None:
                return "data inválida; use AAAA-MM-DD"
        elif t == "data_hora":
            if not data_hora_valida(v):
                return "data e hora inválida; use AAAA-MM-DDThh:mm:ss-03:00"
        elif t in PADRAO_TIPO and not re.match(PADRAO_TIPO[t], v):
            return f"fora do formato ({DESCRICAO_FORMATO_TIPO[t]})"
        if t in TIPOS_DOCUMENTO and not documento_valido(t, v):
            return "dígito verificador inválido"
        if t == "enum" and c.dominio and v not in c.dominio:
            return f"fora do domínio ({', '.join(c.dominio)})"
        if t == "texto":
            if v == "":
                return "texto vazio"
            if c.tamanho_max and len(v) > c.tamanho_max:
                return f"maior que tamanho_max ({c.tamanho_max})"
            if c.formato and not re.search(c.formato, v):
                return f"não atende ao formato {c.formato}"
        return None
    if t == "booleano":
        return None if isinstance(v, bool) else "deve ser true ou false"
    if t in TIPOS_NUMERICOS:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return "deve ser número"
        if t == "inteiro" and not isinstance(v, int):
            return "deve ser número inteiro"
        if c.minimo is not None and v < c.minimo:
            return f"menor que o mínimo {c.minimo}"
        if c.maximo is not None and v > c.maximo:
            return f"maior que o máximo {c.maximo}"
        return None
    return None  # pragma: no cover


def _ler_campo(obj: Any, onde: str, col: _Coletor) -> Campo | None:
    if not isinstance(obj, dict):
        col.erro(f"{onde}: cada campo deve ser um objeto com nome, tipo, obrigatorio e descricao")
        return None
    nome = obj.get("nome")
    if not isinstance(nome, str) or not RE_SNAKE.match(nome):
        col.erro(f"{onde}: nome de campo ausente ou inválido ({nome!r}); use snake_case sem acento")
        return None
    onde = f"{onde} ({nome})"
    _chaves_desconhecidas(obj, CHAVES_CAMPO, onde, col)
    tipo = obj.get("tipo")
    if tipo not in TIPOS:
        col.erro(f"{onde}: tipo {tipo!r} desconhecido; tipos válidos: {', '.join(TIPOS)}")
        return None

    obrig_bruto = obj.get("obrigatorio", False)
    if isinstance(obrig_bruto, bool):
        obrig: bool | Condicao = obrig_bruto
    elif isinstance(obrig_bruto, dict):
        cond = _ler_condicao(obrig_bruto, f"{onde}.obrigatorio", col)
        obrig = cond if cond else False
    else:
        col.erro(f"{onde}: 'obrigatorio' deve ser true, false ou uma condição {{se: campo, igual: valor}}")
        obrig = False

    c = Campo(
        nome=nome, tipo=tipo, obrigatorio=obrig,
        descricao=_texto_opcional(obj.get("descricao")),
        origem=_texto_opcional(obj.get("origem")),
        exemplo=obj.get("exemplo"),
        tamanho_max=obj.get("tamanho_max"),
        formato=obj.get("formato"),
        dominio=obj.get("dominio"),
        referencia=obj.get("referencia"),
        evento=obj.get("evento", False),
        minimo=obj.get("minimo"),
        maximo=obj.get("maximo"),
    )
    if not c.descricao:
        col.aviso(f"{onde}: campo sem descrição")
    if not c.origem:
        col.aviso(f"{onde}: campo sem 'origem' (quem detém o dado hoje)")

    # enum e domínio
    if tipo == "enum":
        if not isinstance(c.dominio, list) or not c.dominio:
            col.erro(f"{onde}: tipo enum exige 'dominio' com a lista de valores aceitos")
            c.dominio = None
        else:
            nao_texto = [v for v in c.dominio if not isinstance(v, str)]
            if nao_texto:
                col.erro(f"{onde}: os valores do domínio devem ser texto; ponha entre aspas: "
                         f"{', '.join(map(repr, nao_texto))}")
            dup = sorted({v for v in c.dominio if c.dominio.count(v) > 1}, key=str)
            if dup:
                col.erro(f"{onde}: valores repetidos no domínio: {', '.join(map(str, dup))}")
            c.dominio = [str(v) for v in c.dominio]
    elif c.dominio is not None:
        col.erro(f"{onde}: 'dominio' só se aplica ao tipo enum")
        c.dominio = None

    # restrições de texto
    if c.tamanho_max is not None:
        if tipo != "texto":
            col.erro(f"{onde}: 'tamanho_max' só se aplica ao tipo texto")
            c.tamanho_max = None
        elif isinstance(c.tamanho_max, bool) or not isinstance(c.tamanho_max, int) or c.tamanho_max < 1:
            col.erro(f"{onde}: 'tamanho_max' deve ser inteiro positivo")
            c.tamanho_max = None
    if c.formato is not None:
        if tipo != "texto":
            col.erro(f"{onde}: 'formato' só se aplica ao tipo texto (os demais tipos já têm formato próprio)")
            c.formato = None
        elif not isinstance(c.formato, str):
            col.erro(f"{onde}: 'formato' deve ser uma expressão regular em texto")
            c.formato = None
        else:
            try:
                re.compile(c.formato)
            except re.error as e:
                col.erro(f"{onde}: expressão regular inválida em 'formato': {e}")
                c.formato = None

    # restrições numéricas
    for lim in ("minimo", "maximo"):
        v = getattr(c, lim)
        if v is None:
            continue
        if tipo not in TIPOS_NUMERICOS:
            col.erro(f"{onde}: '{lim}' só se aplica aos tipos inteiro e decimal")
            setattr(c, lim, None)
        elif isinstance(v, bool) or not isinstance(v, (int, float)):
            col.erro(f"{onde}: '{lim}' deve ser número")
            setattr(c, lim, None)
    if c.minimo is not None and c.maximo is not None and c.minimo > c.maximo:
        col.erro(f"{onde}: 'minimo' ({c.minimo}) maior que 'maximo' ({c.maximo})")

    # evento
    if not isinstance(c.evento, bool):
        col.erro(f"{onde}: 'evento' deve ser true ou false")
        c.evento = False
    elif c.evento and tipo not in TIPOS_DATA:
        col.erro(f"{onde}: 'evento: true' só se aplica aos tipos data e data_hora")
        c.evento = False

    # referência (o destino é conferido depois que todos os blocos forem lidos)
    if c.referencia is not None:
        if not isinstance(c.referencia, str) or c.referencia.count(".") != 1:
            col.erro(f"{onde}: 'referencia' deve ter a forma bloco.campo")
            c.referencia = None

    c.exemplo = _normalizar_exemplo(c)
    return c


def _ler_campos(lista: Any, onde: str, col: _Coletor) -> list[Campo]:
    if lista is None:
        return []
    if not isinstance(lista, list):
        col.erro(f"{onde}: deve ser uma lista de campos")
        return []
    campos: list[Campo] = []
    vistos: set[str] = set()
    for i, obj in enumerate(lista):
        c = _ler_campo(obj, f"{onde}[{i}]", col)
        if c is None:
            continue
        if c.nome in vistos:
            col.erro(f"{onde}: campo {c.nome} definido mais de uma vez")
            continue
        vistos.add(c.nome)
        campos.append(c)
    return campos


def _conferir_condicoes_e_exemplos(campos: list[Campo], onde: str, col: _Coletor) -> None:
    por_nome = {c.nome: c for c in campos}
    for c in campos:
        if isinstance(c.obrigatorio, Condicao):
            cond = c.obrigatorio
            alvo = por_nome.get(cond.campo)
            if alvo is None:
                col.erro(f"{onde}.{c.nome}: a condição de obrigatoriedade cita o campo {cond.campo}, "
                         f"que não existe no mesmo registro")
            elif alvo.nome == c.nome:
                col.erro(f"{onde}.{c.nome}: a condição de obrigatoriedade não pode citar o próprio campo")
            else:
                _conferir_valor_condicao(cond, alvo, f"{onde}.{c.nome}.obrigatorio", col)
        if c.exemplo is not None and not c.automatico:
            prob = problema_valor(c, c.exemplo)
            if prob:
                col.erro(f"{onde}.{c.nome}: exemplo {c.exemplo!r} inválido: {prob}")
        elif c.exemplo is None and not c.automatico:
            col.aviso(f"{onde}.{c.nome}: campo sem 'exemplo'; o envio de exemplo usará um valor genérico")


def _ler_regra(obj: Any, i: int, contrato: Contrato, col: _Coletor) -> Regra | None:
    onde = f"regras[{i}]"
    if not isinstance(obj, dict):
        col.erro(f"{onde}: cada regra deve ser um objeto com id, tipo, severidade e mensagem")
        return None
    rid = obj.get("id")
    if isinstance(rid, str):
        onde = f"regras[{i}] ({rid})"
    _chaves_desconhecidas(obj, CHAVES_REGRA, onde, col)
    ok = True
    if not isinstance(rid, str) or not RE_ID_REGRA.match(rid):
        col.erro(f"{onde}: id {rid!r} inválido; use R06, R09, R10... (rejeição) ou A01, A02... (alerta)")
        ok = False
    elif rid in IDS_RESERVADOS:
        col.erro(f"{onde}: o id {rid} é reservado para uma regra automática "
                 f"({', '.join(sorted(IDS_RESERVADOS))}); use R06, R09 em diante ou A01 em diante")
        ok = False
    tipo = obj.get("tipo")
    if tipo not in TIPOS_REGRA:
        col.erro(f"{onde}: tipo {tipo!r} desconhecido; tipos válidos: {', '.join(TIPOS_REGRA)}")
        ok = False
    sev = obj.get("severidade")
    if sev not in SEVERIDADES:
        col.erro(f"{onde}: severidade {sev!r} inválida; use rejeicao ou alerta")
        ok = False
    mensagem = _texto_opcional(obj.get("mensagem"))
    if not mensagem:
        col.erro(f"{onde}: falta 'mensagem' (texto exibido quando a regra é violada)")
        ok = False
    if ok and rid.startswith("A") and sev == "rejeicao":
        col.aviso(f"{onde}: id iniciado por A costuma indicar alerta, mas a severidade é rejeicao")
    if ok and rid.startswith("R") and sev == "alerta":
        col.aviso(f"{onde}: id iniciado por R costuma indicar rejeição, mas a severidade é alerta")

    bloco = obj.get("bloco", "envio")
    if bloco != "envio" and contrato.bloco(bloco) is None:
        col.erro(f"{onde}: bloco {bloco!r} não existe (blocos: {', '.join(contrato.nomes_blocos)}; "
                 f"use 'envio' para o cabeçalho)")
        ok = False
    if not ok:
        return None

    r = Regra(id=rid, tipo=tipo, severidade=sev, mensagem=mensagem, bloco=bloco)
    campos = {c.nome: c for c in contrato.campos_de(bloco)}

    def exige_campo(chave: str, tipos: tuple[str, ...] | None = None) -> str | None:
        nome = obj.get(chave)
        if not isinstance(nome, str) or not nome:
            col.erro(f"{onde}: falta '{chave}' (nome de campo do bloco {bloco})")
            return None
        if nome not in campos:
            col.erro(f"{onde}: o campo {nome} citado em '{chave}' não existe no bloco {bloco}")
            return None
        if tipos and campos[nome].tipo not in tipos:
            col.erro(f"{onde}: o campo {nome} deve ser do tipo {' ou '.join(tipos)} "
                     f"(é {campos[nome].tipo})")
            return None
        return nome

    if tipo == "ordem_datas":
        r.antes = exige_campo("antes", TIPOS_DATA)
        r.depois = exige_campo("depois", TIPOS_DATA)
        if r.antes and r.antes == r.depois:
            col.erro(f"{onde}: 'antes' e 'depois' citam o mesmo campo")
    elif tipo == "data_minima":
        r.campo = exige_campo("campo", TIPOS_DATA)
        valor = obj.get("valor")
        if isinstance(valor, (date, datetime)):
            valor = (valor.date() if isinstance(valor, datetime) else valor).isoformat()
        if not isinstance(valor, str) or para_data(valor) is None or len(valor) != 10:
            col.erro(f"{onde}: 'valor' deve ser uma data AAAA-MM-DD")
        else:
            r.valor = valor
    elif tipo == "condicional":
        for chave in ("se", "entao"):
            cond = _ler_condicao(obj.get(chave), f"{onde}.{chave}", col, campo_chave="campo")
            if cond is None:
                continue
            if cond.campo not in campos:
                col.erro(f"{onde}.{chave}: o campo {cond.campo} não existe no bloco {bloco}")
                continue
            _conferir_valor_condicao(cond, campos[cond.campo], f"{onde}.{chave}", col)
            setattr(r, chave, cond)
    elif tipo == "expressao":
        texto = obj.get("condicao")
        if not isinstance(texto, str) or not texto.strip():
            col.erro(f"{onde}: falta 'condicao' (expressão que deve ser verdadeira para cada registro)")
        else:
            try:
                r.codigo = compilar_expressao(texto.strip())
                r.condicao = texto.strip()
            except ValueError as e:
                col.erro(f"{onde}: {e}")
    return r


def validar_dados_contrato(dados: Any, caminho: str | None = None) -> Contrato:
    """Valida o conteúdo já lido do YAML e devolve o modelo interno. Levanta ErroContrato."""
    col = _Coletor()
    if not isinstance(dados, dict):
        raise ErroContrato(["o arquivo deve conter um objeto YAML (chave: valor) no nível principal"], caminho)
    _chaves_desconhecidas(dados, CHAVES_TOPO, "contrato", col)

    nome = dados.get("contrato")
    if not isinstance(nome, str) or not RE_NOME_CONTRATO.match(nome):
        col.erro(f"'contrato' ausente ou inválido ({nome!r}); use minúsculas, dígitos e hífen (ex.: ipg-envio)")
        nome = str(nome or "contrato")
    versao = dados.get("versao")
    if isinstance(versao, float):
        col.erro(f"'versao' foi lida como número ({versao}); escreva entre aspas, ex.: versao: \"1.0\"")
        versao = str(versao)
    elif not isinstance(versao, str) or not RE_VERSAO.match(versao):
        col.erro(f"'versao' ausente ou inválida ({versao!r}); use MAIOR.MENOR entre aspas, ex.: \"1.0\"")
        versao = str(versao or "0.0")
    titulo = _texto_opcional(dados.get("titulo"))
    if not titulo:
        col.erro("falta 'titulo' (nome curto da coleta)")
    descricao = _texto_opcional(dados.get("descricao"))
    if not descricao:
        col.aviso("falta 'descricao' (finalidade da coleta)")
    orgao = _texto_opcional(dados.get("orgao"))
    if not orgao:
        col.aviso("falta 'orgao' (agência que define o padrão)")

    regulados = dados.get("regulados")
    if not isinstance(regulados, list) or not regulados:
        col.erro("'regulados' deve ser uma lista não vazia (vira o domínio do campo remetente)")
        regulados = []
    else:
        if any(not isinstance(r, str) or not r for r in regulados):
            col.erro("'regulados': cada item deve ser um texto não vazio")
        regulados = [str(r) for r in regulados]
        if len(set(regulados)) != len(regulados):
            col.erro("'regulados': há itens repetidos")

    base = dados.get("base_normativa") or []
    if not isinstance(base, list):
        col.erro("'base_normativa' deve ser uma lista de {id, descricao, url}")
        base = []
    for i, b in enumerate(base):
        if not isinstance(b, dict) or not b.get("id") or not b.get("descricao"):
            col.erro(f"base_normativa[{i}]: cada norma precisa de 'id' e 'descricao'")
    base = [b for b in base if isinstance(b, dict)]

    teste = dados.get("teste_auditoria") or {}
    lacunas: list[Lacuna] = []
    if not isinstance(teste, dict):
        col.erro("'teste_auditoria' deve ser um objeto com pergunta, regra, classificacao, saidas e lacunas")
        teste = {}
    else:
        if not teste:
            col.aviso("falta 'teste_auditoria' (pergunta, regra, classificação e lacunas)")
        if teste and teste.get("classificacao") not in CLASSIFICACOES:
            col.erro(f"teste_auditoria.classificacao {teste.get('classificacao')!r} inválida; "
                     f"use {', '.join(CLASSIFICACOES)}")
        saidas = teste.get("saidas")
        if saidas is not None and (not isinstance(saidas, list) or not all(isinstance(s, str) for s in saidas)):
            col.erro("teste_auditoria.saidas deve ser uma lista de textos")
        lac = teste.get("lacunas") or []
        if not isinstance(lac, list):
            col.erro("teste_auditoria.lacunas deve ser uma lista")
            lac = []
        ids_lac: set[str] = set()
        for i, l in enumerate(lac):
            if not isinstance(l, dict) or not l.get("id"):
                col.erro(f"teste_auditoria.lacunas[{i}]: cada lacuna precisa de 'id'")
                continue
            if l["id"] in ids_lac:
                col.erro(f"teste_auditoria.lacunas: id {l['id']} repetido")
            ids_lac.add(l["id"])
            lacunas.append(Lacuna(str(l["id"]), _texto_opcional(l.get("trecho")),
                                  _texto_opcional(l.get("problema")),
                                  _texto_opcional(l.get("decisao_padrao")),
                                  _texto_opcional(l.get("quem_decide"))))

    period = dados.get("periodicidade") or {}
    if not isinstance(period, dict):
        col.erro("'periodicidade' deve ser um objeto com carga_inicial, regular e prazo_entrega")
        period = {}
    elif period.get("regular") is not None and period.get("regular") not in PERIODICIDADES:
        col.erro(f"periodicidade.regular {period.get('regular')!r} inválida; use {', '.join(PERIODICIDADES)}")

    cab_auto = _cabecalho_automatico(nome, versao, regulados)
    cab_contrato = _ler_campos(dados.get("cabecalho"), "cabecalho", col)
    nomes_auto = set(NOMES_CABECALHO_AUTOMATICO) | {"totais"}
    for c in cab_contrato:
        if c.nome in nomes_auto:
            col.erro(f"cabecalho.{c.nome}: nome reservado ao cabeçalho automático "
                     f"({', '.join(sorted(nomes_auto))})")
        if c.referencia:
            col.erro(f"cabecalho.{c.nome}: 'referencia' não se aplica a campos do cabeçalho")
            c.referencia = None
    cab_contrato = [c for c in cab_contrato if c.nome not in nomes_auto]
    cabecalho = cab_auto + cab_contrato
    _conferir_condicoes_e_exemplos(cabecalho, "cabecalho", col)

    blocos: list[Bloco] = []
    lista_blocos = dados.get("blocos")
    if not isinstance(lista_blocos, list) or not lista_blocos:
        col.erro("'blocos' deve ser uma lista não vazia de blocos de dados")
        lista_blocos = []
    vistos: set[str] = set()
    for i, ob in enumerate(lista_blocos):
        onde = f"blocos[{i}]"
        if not isinstance(ob, dict):
            col.erro(f"{onde}: cada bloco deve ser um objeto com nome, descricao, chave e campos")
            continue
        bnome = ob.get("nome")
        if not isinstance(bnome, str) or not RE_SNAKE.match(bnome):
            col.erro(f"{onde}: nome de bloco ausente ou inválido ({bnome!r}); use snake_case sem acento")
            continue
        onde = f"blocos.{bnome}"
        _chaves_desconhecidas(ob, CHAVES_BLOCO, onde, col)
        if bnome in NOMES_RESERVADOS_BLOCO:
            col.erro(f"{onde}: o nome {bnome} é reservado ao cabeçalho do envio")
            continue
        if bnome in vistos:
            col.erro(f"{onde}: bloco definido mais de uma vez")
            continue
        vistos.add(bnome)
        campos = _ler_campos(ob.get("campos"), f"{onde}.campos", col)
        if not campos:
            col.erro(f"{onde}: o bloco precisa de ao menos um campo")
        chave = ob.get("chave")
        if chave is None:
            col.aviso(f"{onde}: bloco sem 'chave'; a unicidade (R02) não será conferida")
            chave = []
        elif isinstance(chave, str):
            chave = [chave]
        if not isinstance(chave, list) or not all(isinstance(k, str) for k in chave):
            col.erro(f"{onde}: 'chave' deve ser uma lista de nomes de campo")
            chave = []
        nomes = {c.nome for c in campos}
        for k in chave:
            if k not in nomes:
                col.erro(f"{onde}: o campo de chave {k} não existe no bloco")
            elif next(c for c in campos if c.nome == k).obrigatorio is not True:
                col.aviso(f"{onde}: o campo de chave {k} não é obrigatório; registros sem ele ficam fora da R02")
        if len(set(chave)) != len(chave):
            col.erro(f"{onde}: a chave repete campos")
        _conferir_condicoes_e_exemplos(campos, onde, col)
        blocos.append(Bloco(bnome, _texto_opcional(ob.get("descricao")), [k for k in chave if k in nomes], campos))
        if not _texto_opcional(ob.get("descricao")):
            col.aviso(f"{onde}: bloco sem descrição")

    # referências entre blocos
    por_bloco = {b.nome: b for b in blocos}
    for b in blocos:
        for c in b.campos:
            if not c.referencia:
                continue
            bref, cref = c.referencia.split(".", 1)
            alvo = por_bloco.get(bref)
            if alvo is None:
                col.erro(f"blocos.{b.nome}.{c.nome}: a referência {c.referencia} cita o bloco {bref}, que não existe")
                continue
            campo_alvo = alvo.campo(cref)
            if campo_alvo is None:
                col.erro(f"blocos.{b.nome}.{c.nome}: a referência {c.referencia} cita o campo {cref}, "
                         f"que não existe no bloco {bref}")
                continue
            if bref == b.nome and cref == c.nome:
                col.erro(f"blocos.{b.nome}.{c.nome}: o campo não pode referenciar a si mesmo")
            if campo_alvo.tipo != c.tipo:
                col.aviso(f"blocos.{b.nome}.{c.nome}: tipo {c.tipo} diferente do campo referenciado "
                          f"{c.referencia} ({campo_alvo.tipo})")

    contrato = Contrato(
        contrato=nome, versao=versao, titulo=titulo, descricao=descricao, orgao=orgao,
        regulados=regulados, base_normativa=base, teste_auditoria=teste, lacunas=lacunas,
        periodicidade=period, cabecalho=cabecalho, blocos=blocos, regras=[], caminho=caminho,
    )

    regras_brutas = dados.get("regras") or []
    if not isinstance(regras_brutas, list):
        col.erro("'regras' deve ser uma lista")
        regras_brutas = []
    ids: set[str] = set()
    for i, ob in enumerate(regras_brutas):
        r = _ler_regra(ob, i, contrato, col)
        if r is None:
            continue
        if r.id in ids:
            col.erro(f"regras[{i}]: id {r.id} repetido; cada regra precisa de id único")
            continue
        ids.add(r.id)
        contrato.regras.append(r)

    if col.erros:
        raise ErroContrato(col.erros, caminho)
    contrato.avisos = col.avisos
    return contrato


def carregar_contrato(caminho: str | Path) -> Contrato:
    """Lê o arquivo YAML do contrato, valida e devolve o modelo interno. Levanta ErroContrato."""
    if yaml is None:  # pragma: no cover
        raise ErroContrato(["a biblioteca pyyaml não está instalada (pip install --user pyyaml)"], str(caminho))
    p = Path(caminho)
    try:
        texto = p.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ErroContrato([f"arquivo não encontrado: {p}"], str(p)) from None
    except UnicodeDecodeError:
        raise ErroContrato(["o arquivo não está em UTF-8"], str(p)) from None
    try:
        dados = yaml.safe_load(texto)
    except yaml.YAMLError as e:
        raise ErroContrato([f"YAML malformado: {e}"], str(p)) from None
    return validar_dados_contrato(dados, str(p))


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:  # pragma: no cover
            pass
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("Uso: python ferramentas/contrato.py caminho/contrato.yaml", file=sys.stderr)
        return 2
    try:
        c = carregar_contrato(args[0])
    except ErroContrato as e:
        print(e, file=sys.stderr)
        return 1
    print(f"Contrato {c.contrato} versão {c.versao} válido: {len(c.blocos)} bloco(s), "
          f"{sum(len(b.campos) for b in c.blocos)} campo(s), {len(c.regras)} regra(s) adicionais.")
    for a in c.avisos:
        print(f"  aviso: {a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
