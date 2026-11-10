# -*- coding: utf-8 -*-
"""
Gera a especificação OpenAPI 3.1 da API de consulta (modelo pull: o regulado expõe,
a agência consulta) a partir do contrato de coleta.

  GET /envios/{data_referencia}   cabeçalho do envio na data de corte, com os totais
  GET /<bloco>                    registros do bloco, com data_referencia, alterado_desde,
                                  limite e cursor; resposta {dados, proximo_cursor, total}

Autenticação OAuth2 client credentials; erros no formato RFC 9457 (application/problem+json);
servidor fictício (exemplo.invalid), a ser substituído pelo endereço real do regulado.
Os schemas espelham o JSON Schema gerado (mesmos campos, tipos, domínios e obrigatoriedades).
"""
from __future__ import annotations

import copy
from typing import Any

from contrato import Contrato
from gerador_schema import gerar_schema

TIPO_PROBLEMA = "application/problem+json"


def _trocar_refs(no: Any) -> Any:
    if isinstance(no, dict):
        return {k: (v.replace("#/$defs/", "#/components/schemas/") if k == "$ref" and isinstance(v, str)
                    else _trocar_refs(v)) for k, v in no.items()}
    if isinstance(no, list):
        return [_trocar_refs(v) for v in no]
    return no


def _erros(*codigos: str) -> dict[str, Any]:
    textos = {
        "400": "Parâmetro inválido",
        "401": "Não autenticado (token ausente ou expirado)",
        "403": "Sem permissão para o escopo solicitado",
        "404": "Não há dados para a data de referência informada",
        "429": "Limite de requisições excedido",
        "500": "Erro interno do servidor",
        "503": "Serviço indisponível",
    }
    return {c: {"description": textos[c], "content": {TIPO_PROBLEMA: {"schema": {"$ref": "#/components/schemas/Problema"}}}}
            for c in codigos}


def gerar_openapi(contrato: Contrato) -> dict[str, Any]:
    schema = gerar_schema(contrato)
    componentes = _trocar_refs(copy.deepcopy(schema["$defs"]))
    escopo = f"{contrato.contrato}.leitura"
    componentes["Problema"] = {
        "title": "Problema (RFC 9457)",
        "description": "Detalhe de erro no formato Problem Details for HTTP APIs (RFC 9457).",
        "type": "object",
        "required": ["title", "status"],
        "properties": {
            "type": {"type": "string", "format": "uri", "description": "URI que identifica o tipo do problema.",
                     "default": "about:blank"},
            "title": {"type": "string", "description": "Resumo legível do problema."},
            "status": {"type": "integer", "description": "Código HTTP."},
            "detail": {"type": "string", "description": "Explicação específica desta ocorrência."},
            "instance": {"type": "string", "description": "URI da ocorrência."},
            "erros": {
                "type": "array", "description": "Lista de parâmetros ou campos com problema.",
                "items": {"type": "object", "properties": {"parametro": {"type": "string"},
                                                           "mensagem": {"type": "string"}}},
            },
        },
    }

    p_data_ref = {
        "name": "data_referencia", "in": "query", "required": True,
        "description": "Data de corte (AAAA-MM-DD): devolve a posição dos dados até este dia, inclusive.",
        "schema": {"type": "string", "format": "date"},
    }
    p_alterado = {
        "name": "alterado_desde", "in": "query", "required": False,
        "description": "Só registros criados ou alterados a partir deste instante (ISO 8601 com fuso). "
                       "Usado para a carga INCREMENTAL.",
        "schema": {"type": "string", "format": "date-time"},
    }
    p_limite = {
        "name": "limite", "in": "query", "required": False,
        "description": "Quantidade máxima de registros por página.",
        "schema": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 500},
    }
    p_cursor = {
        "name": "cursor", "in": "query", "required": False,
        "description": "Cursor opaco devolvido em proximo_cursor pela página anterior.",
        "schema": {"type": "string"},
    }

    paths: dict[str, Any] = {
        "/envios/{data_referencia}": {
            "get": {
                "tags": ["Envio"],
                "operationId": "obterEnvio",
                "summary": "Cabeçalho do envio na data de corte",
                "description": (
                    "Devolve o objeto `envio` para a data de referência, com os `totais` de cada bloco "
                    "(conferidos pela regra R08). Sem `data_referencia_anterior`, a carga é COMPLETA; com "
                    "ela, INCREMENTAL, e os totais contam só o que mudou desde o envio anterior."
                ),
                "parameters": [
                    {"name": "data_referencia", "in": "path", "required": True,
                     "description": "Data de corte (AAAA-MM-DD).", "schema": {"type": "string", "format": "date"}},
                    {"name": "data_referencia_anterior", "in": "query", "required": False,
                     "description": "Data de referência do envio anterior (carga INCREMENTAL).",
                     "schema": {"type": "string", "format": "date"}},
                ],
                "responses": {
                    "200": {"description": "Cabeçalho do envio.",
                            "headers": {"X-Versao-Layout": {"description": "Versão do layout de dados.",
                                                            "schema": {"type": "string", "const": contrato.versao}}},
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Envio"}}}},
                    **_erros("400", "401", "403", "404", "429", "500", "503"),
                },
            }
        }
    }
    tags = [{"name": "Envio", "description": "Cabeçalho do envio e totais para conferência."}]
    for b in contrato.blocos:
        tags.append({"name": b.nome, "description": b.descricao or b.nome})
        paths[f"/{b.nome}"] = {
            "get": {
                "tags": [b.nome],
                "operationId": "listar_" + b.nome,
                "summary": f"Registros do bloco {b.nome}",
                "description": (b.descricao + "\n\n" if b.descricao else "") +
                "Paginação por cursor: repita a chamada com `cursor = proximo_cursor` até que ele venha nulo.",
                "parameters": [p_data_ref, p_alterado, p_limite, p_cursor],
                "responses": {
                    "200": {
                        "description": f"Página de registros do bloco {b.nome}.",
                        "content": {"application/json": {"schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["dados", "proximo_cursor", "total"],
                            "properties": {
                                "dados": {"type": "array", "items": {"$ref": f"#/components/schemas/{b.nome}"}},
                                "proximo_cursor": {"type": ["string", "null"],
                                                   "description": "Cursor da próxima página; null na última."},
                                "total": {"type": "integer", "minimum": 0,
                                          "description": "Total de registros na consulta (todas as páginas)."},
                            },
                        }}},
                    },
                    **_erros("400", "401", "403", "429", "500", "503"),
                },
            }
        }

    descricao = (contrato.descricao or contrato.titulo).strip()
    pergunta = str((contrato.teste_auditoria or {}).get("pergunta", "")).strip()
    texto = (
        f"{descricao}\n\n"
        + (f"**Teste de auditoria.** {pergunta}\n\n" if pergunta else "")
        + f"**Modelo de operação.** A API é exposta pelo regulado ({', '.join(contrato.regulados)}) e "
        f"consultada por {contrato.orgao or 'a agência'} (modelo pull, só leitura).\n\n"
        f"**Contrato de dados.** Campos, tipos, domínios e regras seguem o contrato de coleta "
        f"`{contrato.contrato}` versão {contrato.versao}, o mesmo usado nos canais JSON e Excel.\n\n"
        "**Servidor.** O endereço abaixo é fictício e deve ser substituído pelo do regulado."
    )
    return {
        "openapi": "3.1.0",
        "info": {
            "title": f"{contrato.titulo} — API de consulta",
            "version": contrato.versao,
            "summary": f"Consulta dos dados do contrato de coleta {contrato.contrato}.",
            "description": texto,
        },
        "jsonSchemaDialect": "https://json-schema.org/draft/2020-12/schema",
        "servers": [{"url": f"https://api.regulado.exemplo.invalid/{contrato.contrato}/v{contrato.versao_maior}",
                     "description": "Servidor fictício (substituir pelo endereço do regulado)"}],
        "security": [{"oauth2": [escopo]}],
        "tags": tags,
        "paths": paths,
        "components": {
            "securitySchemes": {
                "oauth2": {
                    "type": "oauth2",
                    "description": "OAuth 2.0 client credentials; a agência recebe client_id e client_secret do regulado.",
                    "flows": {"clientCredentials": {
                        "tokenUrl": "https://auth.regulado.exemplo.invalid/oauth2/token",
                        "scopes": {escopo: f"Leitura dos dados do contrato {contrato.contrato}"},
                    }},
                }
            },
            "schemas": componentes,
        },
    }
