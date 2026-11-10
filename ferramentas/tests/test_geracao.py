# -*- coding: utf-8 -*-
"""Geração dos artefatos: schema, Excel, OpenAPI, dicionário e exemplo."""
import json

import pytest
import yaml
from jsonschema import Draft202012Validator
from openpyxl import load_workbook

from conftest import CONTRATO_MINIMO
from gerar_padrao import gerar_tudo, main as gerar_main
from validar_envio import validar_arquivo, validar_documento


@pytest.fixture(scope="module")
def gerados(contrato, tmp_path_factory):
    pasta = tmp_path_factory.mktemp("gerado")
    return gerar_tudo(contrato, pasta)


def test_todos_os_artefatos_gerados(gerados):
    nomes = {p.name for p in gerados.values()}
    assert nomes == {
        "fiscalizacao-teste-1.0.schema.json", "modelo_fiscalizacao-teste_v1.0.xlsx", "openapi.yaml",
        "dicionario_de_dados.md", "exemplo_envio.json",
    }
    for p in gerados.values():
        assert p.stat().st_size > 0


def test_schema_valido_2020_12(gerados):
    schema = json.loads(gerados["schema"].read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["additionalProperties"] is False
    assert set(schema["$defs"]) == {"Envio", "Totais", "estabelecimentos", "fiscalizacoes"}
    est = schema["$defs"]["estabelecimentos"]
    assert est["additionalProperties"] is False
    assert est["properties"]["situacao"]["enum"] == ["ATIVO", "BAIXADO"]
    assert est["properties"]["id_estabelecimento"]["pattern"] == "^EST-[0-9]{4}$"
    cond = est["allOf"][0]
    assert cond["if"]["properties"]["situacao"]["const"] == "BAIXADO"
    assert cond["then"]["required"] == ["motivo_baixa"]
    envio = schema["$defs"]["Envio"]
    inc = next(x for x in envio["allOf"] if "data_referencia_anterior" in x["then"]["required"])
    assert inc["if"]["properties"]["tipo_carga"]["const"] == "INCREMENTAL"
    assert envio["properties"]["remetente"]["enum"] == ["REGULADO_A", "REGULADO_B"]


def test_openapi_valido(gerados):
    spec = yaml.safe_load(gerados["openapi"].read_text(encoding="utf-8"))
    assert spec["openapi"] == "3.1.0"
    validador = pytest.importorskip("openapi_spec_validator")
    validador.validate(spec)
    assert "/envios/{data_referencia}" in spec["paths"]
    for bloco in ("estabelecimentos", "fiscalizacoes"):
        op = spec["paths"][f"/{bloco}"]["get"]
        nomes = {p["name"] for p in op["parameters"]}
        assert nomes == {"data_referencia", "alterado_desde", "limite", "cursor"}
        resp = op["responses"]["200"]["content"]["application/json"]["schema"]
        assert set(resp["properties"]) == {"dados", "proximo_cursor", "total"}
        assert "application/problem+json" in op["responses"]["400"]["content"]
    fluxos = spec["components"]["securitySchemes"]["oauth2"]["flows"]
    assert "clientCredentials" in fluxos
    assert "Problema" in spec["components"]["schemas"]
    assert "$defs" not in gerados["openapi"].read_text(encoding="utf-8")


def test_excel_estrutura(gerados, contrato):
    wb = load_workbook(gerados["excel"])
    assert wb.sheetnames == ["LEIA-ME", "envio", "estabelecimentos", "fiscalizacoes", "dicionario", "listas"]
    assert wb["listas"].sheet_state == "hidden"
    ws = wb["estabelecimentos"]
    assert [c.value for c in ws[1]] == contrato.bloco("estabelecimentos").nomes
    assert "tbl_estabelecimentos" in ws.tables
    assert ws.freeze_panes == "A2"
    assert ws["A1"].comment is not None
    # cores: obrigatório (azul), condicional (laranja), opcional (cinza)
    cores = {c.value: c.fill.fgColor.rgb[-6:] for c in ws[1]}
    assert cores["id_estabelecimento"] == "1F4E79"
    assert cores["motivo_baixa"] == "C55A11"
    assert cores["codigo_ibge_municipio"] == "7F7F7F"
    tipos_dv = {dv.type for dv in ws.data_validations.dataValidation}
    assert {"list", "date", "textLength"} <= tipos_dv
    env = wb["envio"]
    campos = [env.cell(row=i, column=1).value for i in range(2, env.max_row + 1)]
    assert "totais.estabelecimentos" in campos and "remetente" in campos
    assert env.freeze_panes == "B2"
    assert any(dv.type == "list" for dv in wb["fiscalizacoes"].data_validations.dataValidation)


def test_dicionario(gerados):
    md = gerados["dicionario"].read_text(encoding="utf-8")
    for trecho in ("## Bloco `estabelecimentos`", "## Teste de auditoria", "### Lacunas", "| R06 |",
                   "Origem (quem detém)", "Se situacao = BAIXADO", "## Cabeçalho (`envio`)"):
        assert trecho in md


def test_exemplo_gerado_aceito(gerados, contrato):
    rel, doc = validar_arquivo(contrato, gerados["exemplo"])
    assert rel.situacao == "ACEITO", rel.como_texto()
    assert 2 <= len(doc["estabelecimentos"]) <= 3
    assert doc["envio"]["totais"] == {"estabelecimentos": len(doc["estabelecimentos"]),
                                      "fiscalizacoes": len(doc["fiscalizacoes"])}


def test_cli_gerar(tmp_path, capsys):
    assert gerar_main([str(CONTRATO_MINIMO), "--saida", str(tmp_path)]) == 0
    assert "ACEITO" in capsys.readouterr().out
    assert (tmp_path / "openapi.yaml").exists()


def test_cli_gerar_contrato_invalido(tmp_path, capsys):
    ruim = tmp_path / "ruim.yaml"
    ruim.write_text("contrato: x\nversao: '1.0'\ntitulo: t\nregulados: [A]\nblocos: []\n", encoding="utf-8")
    assert gerar_main([str(ruim), "--saida", str(tmp_path / "s")]) == 2
    assert "Contrato inválido" in capsys.readouterr().err
    assert not (tmp_path / "s").exists()


def test_exemplo_com_valores_genericos():
    """Sem nenhum `exemplo`, o gerador ainda produz um envio aceito."""
    texto = CONTRATO_MINIMO.read_text(encoding="utf-8")
    d = yaml.safe_load(texto)
    for b in d["blocos"]:
        for c in b["campos"]:
            c.pop("exemplo", None)
            c.pop("formato", None)
    d["cabecalho"][0].pop("exemplo")
    from contrato import validar_dados_contrato
    from gerador_exemplo import gerar_exemplo
    c2 = validar_dados_contrato(d)
    rel = validar_documento(c2, gerar_exemplo(c2))
    assert not rel.rejeitado, rel.como_texto()


CASO_IPG = CONTRATO_MINIMO.parents[2] / "exemplos" / "ipg-gas-rj"


@pytest.mark.skipif(not (CASO_IPG / "contrato.yaml").exists(), reason="caso-exemplo ausente")
def test_caso_exemplo_ipg(tmp_path):
    """Integração com o caso real do repositório: gera tudo e valida os envios de exemplo."""
    from contrato import carregar_contrato
    c = carregar_contrato(CASO_IPG / "contrato.yaml")
    caminhos = gerar_tudo(c, tmp_path)
    Draft202012Validator.check_schema(json.loads(caminhos["schema"].read_text(encoding="utf-8")))
    rel, _ = validar_arquivo(c, caminhos["exemplo"])
    assert not rel.rejeitado, rel.como_texto()
    envios = CASO_IPG / "envios"
    for nome in ("exemplo_envio_completo.json", "exemplo_envio_incremental.json"):
        if (envios / nome).exists():
            rel, _ = validar_arquivo(c, envios / nome)
            assert not rel.rejeitado, rel.como_texto()
