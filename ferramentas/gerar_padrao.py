# -*- coding: utf-8 -*-
"""
Gera os padrões de coleta a partir do contrato de coleta.

Uso:
  python ferramentas/gerar_padrao.py caminho/contrato.yaml --saida pasta/

Arquivos gerados na pasta de saída:
  <contrato>-<versao>.schema.json     JSON Schema 2020-12 do envio
  modelo_<contrato>_v<versao>.xlsx    planilha-modelo (canal Excel)
  openapi.yaml                        especificação OpenAPI 3.1 da API de consulta
  dicionario_de_dados.md              dicionário de dados e regras
  exemplo_envio.json                  envio sintético válido (conferido pelo validador)

Códigos de saída:
  0  artefatos gerados e envio de exemplo aceito
  1  artefatos gerados, mas o envio de exemplo foi rejeitado (revise os `exemplo` do contrato)
  2  erro de uso ou contrato inválido (nada é gerado)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from contrato import Contrato, ErroContrato, carregar_contrato
from gerador_dicionario import gerar_dicionario
from gerador_excel import gerar_excel, nome_arquivo_excel
from gerador_exemplo import gerar_exemplo
from gerador_openapi import gerar_openapi
from gerador_schema import gerar_schema


class _DumperLegivel(yaml.SafeDumper):
    """Dumper que não usa âncoras/aliases (o YAML fica autocontido e legível)."""

    def ignore_aliases(self, data):  # noqa: ANN001
        return True


def _str_bloco(dumper, dado: str):
    estilo = "|" if "\n" in dado else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", dado, style=estilo)


_DumperLegivel.add_representer(str, _str_bloco)


def gerar_tudo(contrato: Contrato, saida: Path) -> dict[str, Path]:
    """Gera todos os artefatos e devolve {tipo: caminho}."""
    saida.mkdir(parents=True, exist_ok=True)
    caminhos: dict[str, Path] = {}

    p = saida / f"{contrato.nome_base}.schema.json"
    p.write_text(json.dumps(gerar_schema(contrato), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    caminhos["schema"] = p

    caminhos["excel"] = gerar_excel(contrato, saida / nome_arquivo_excel(contrato))

    p = saida / "openapi.yaml"
    p.write_text(yaml.dump(gerar_openapi(contrato), Dumper=_DumperLegivel, allow_unicode=True,
                           sort_keys=False, width=110), encoding="utf-8")
    caminhos["openapi"] = p

    p = saida / "dicionario_de_dados.md"
    p.write_text(gerar_dicionario(contrato), encoding="utf-8")
    caminhos["dicionario"] = p

    p = saida / "exemplo_envio.json"
    p.write_text(json.dumps(gerar_exemplo(contrato), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    caminhos["exemplo"] = p
    return caminhos


def main(argv: list[str] | None = None) -> int:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except AttributeError:  # pragma: no cover
            pass
    ap = argparse.ArgumentParser(description="Gera JSON Schema, modelo Excel, OpenAPI, dicionário de dados "
                                             "e envio de exemplo a partir do contrato de coleta.")
    ap.add_argument("contrato", type=Path, help="caminho do contrato.yaml")
    ap.add_argument("--saida", type=Path, default=Path("gerado"), help="pasta de saída (padrão: ./gerado)")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 2

    try:
        contrato = carregar_contrato(args.contrato)
    except ErroContrato as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    for a in contrato.avisos:
        print(f"aviso: {a}")

    caminhos = gerar_tudo(contrato, args.saida)
    print(f"Contrato {contrato.contrato} {contrato.versao}: artefatos gerados em {args.saida}")
    for p in caminhos.values():
        print(f"  - {p.name}")

    from validar_envio import validar_arquivo
    rel, _ = validar_arquivo(contrato, caminhos["exemplo"])
    if rel.rejeitado:
        print("\nATENÇÃO: o envio de exemplo gerado foi REJEITADO pelo validador. Revise os 'exemplo' "
              "dos campos (e as regras do contrato):", file=sys.stderr)
        print(rel.como_texto(), file=sys.stderr)
        return 1
    print(f"Envio de exemplo conferido pelo validador: {rel.situacao}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
