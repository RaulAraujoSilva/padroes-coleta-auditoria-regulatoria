# -*- coding: utf-8 -*-
"""Validação de envios: cada regra automática e cada tipo de regra do contrato."""
import gzip
import hashlib
import json
import zipfile

import pytest

from conftest import CONTRATO_MINIMO
from validar_envio import main as validar_main, validar_documento


def regras_violadas(contrato, doc):
    rel = validar_documento(contrato, doc)
    return rel, {r for r, lst in rel.ocorrencias.items() if lst}


def test_exemplo_aceito(contrato, exemplo):
    rel, violadas = regras_violadas(contrato, exemplo)
    assert violadas == set(), rel.como_texto()
    assert rel.situacao == "ACEITO"


# ----------------------------------------------------------------- regras automáticas

def test_r01_enum_fora_do_dominio(contrato, exemplo):
    exemplo["estabelecimentos"][0]["situacao"] = "SUSPENSO"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R01"}
    o = rel.ocorrencias["R01"][0]
    assert o.bloco == "estabelecimentos" and o.campo == "situacao" and "id_estabelecimento=EST-0001" in o.chave


def test_r01_obrigatorio_ausente(contrato, exemplo):
    del exemplo["fiscalizacoes"][1]["data_fiscalizacao"]
    rel, v = regras_violadas(contrato, exemplo)
    assert "R01" in v
    assert rel.ocorrencias["R01"][0].campo == "data_fiscalizacao"


def test_r01_formato_tipo_e_campo_extra(contrato, exemplo):
    exemplo["estabelecimentos"][0]["cnpj"] = "11.222.333/0001-81"
    exemplo["fiscalizacoes"][0]["prazo_dias"] = "trinta"
    exemplo["fiscalizacoes"][1]["campo_novo"] = 1
    exemplo["estabelecimentos"][1]["data_abertura"] = "2021-02-30"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R01"}
    assert rel.contagem("R01") == 4


def test_r01_constante_do_cabecalho(contrato, exemplo):
    exemplo["envio"]["versao_layout"] = "9.9"
    _, v = regras_violadas(contrato, exemplo)
    assert v == {"R01"}


def test_r02_chave_repetida(contrato, exemplo):
    exemplo["fiscalizacoes"][1]["id_fiscalizacao"] = exemplo["fiscalizacoes"][0]["id_fiscalizacao"]
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R02"}
    assert rel.ocorrencias["R02"][0].bloco == "fiscalizacoes"


def test_r03_referencia_inexistente(contrato, exemplo):
    exemplo["fiscalizacoes"][0]["id_estabelecimento"] = "EST-9999"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R03", "A02"}          # A02: EST-0001 ficou sem fiscalização (efeito esperado)
    assert rel.ocorrencias["R03"][0].campo == "id_estabelecimento"


def test_r03_nao_se_aplica_na_incremental(contrato, exemplo):
    exemplo["fiscalizacoes"][0]["id_estabelecimento"] = "EST-9999"
    exemplo["envio"]["tipo_carga"] = "INCREMENTAL"
    exemplo["envio"]["data_referencia_anterior"] = "2020-01-01"
    rel, v = regras_violadas(contrato, exemplo)
    assert "R03" not in v and not rel.rejeitado
    assert any("INCREMENTAL" in o for o in rel.observacoes)


def test_r04_evento_depois_da_data_referencia(contrato, exemplo):
    exemplo["estabelecimentos"][2]["data_abertura"] = "2099-01-01"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R04"}
    assert rel.ocorrencias["R04"][0].campo == "data_abertura"


def test_r04_data_referencia_anterior_nao_anterior(contrato, exemplo):
    exemplo["envio"]["tipo_carga"] = "INCREMENTAL"
    exemplo["envio"]["data_referencia_anterior"] = exemplo["envio"]["data_referencia"]
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R04"}
    assert rel.ocorrencias["R04"][0].campo == "data_referencia_anterior"


def test_r05_obrigatoriedade_condicional(contrato, exemplo):
    exemplo["estabelecimentos"][0]["situacao"] = "BAIXADO"
    del exemplo["estabelecimentos"][0]["motivo_baixa"]
    exemplo["fiscalizacoes"][0]["valor_multa"] = None
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R05"}
    campos = {o.campo for o in rel.ocorrencias["R05"]}
    assert campos == {"motivo_baixa", "valor_multa"}
    assert "BAIXADO" in rel.ocorrencias["R05"][0].mensagem + rel.ocorrencias["R05"][1].mensagem


def test_r05_opcional_ausente_quando_condicao_falsa(contrato, exemplo):
    del exemplo["estabelecimentos"][0]["motivo_baixa"]          # situacao = ATIVO
    _, v = regras_violadas(contrato, exemplo)
    assert v == set()


def test_r05_incremental_sem_data_anterior(contrato, exemplo):
    exemplo["envio"]["tipo_carga"] = "INCREMENTAL"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R05"}
    assert rel.ocorrencias["R05"][0].campo == "data_referencia_anterior"


def test_r07_digito_verificador(contrato, exemplo):
    exemplo["estabelecimentos"][0]["cnpj"] = "11222333000182"
    exemplo["estabelecimentos"][1]["cpf_responsavel"] = "52998224726"
    exemplo["envio"]["cnpj_remetente"] = "11222333000100"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R07"}
    assert rel.contagem("R07") == 3


def test_r08_totais(contrato, exemplo):
    exemplo["envio"]["totais"]["fiscalizacoes"] += 5
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R08"}


# ----------------------------------------------------------------- regras do contrato

def test_ordem_datas(contrato, exemplo):
    f = exemplo["fiscalizacoes"][0]
    f["data_relatorio"] = "2020-06-01"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R06"} and rel.rejeitado


def test_data_minima_e_alerta(contrato, exemplo):
    exemplo["fiscalizacoes"][0]["data_fiscalizacao"] = "2019-12-31"
    exemplo["fiscalizacoes"][0]["data_relatorio"] = "2020-01-05"
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"A01"}
    assert rel.situacao == "ACEITO COM ALERTAS"


def test_condicional(contrato, exemplo):
    del exemplo["fiscalizacoes"][2]["prazo_dias"]     # resultado = AUTUADO
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"R09"} and rel.rejeitado
    assert rel.ocorrencias["R09"][0].campo == "prazo_dias"


def test_expressao_com_gerador(contrato, exemplo):
    exemplo["fiscalizacoes"] = [f for f in exemplo["fiscalizacoes"]
                                if f["id_estabelecimento"] != exemplo["estabelecimentos"][0]["id_estabelecimento"]]
    exemplo["envio"]["totais"]["fiscalizacoes"] = len(exemplo["fiscalizacoes"])
    rel, v = regras_violadas(contrato, exemplo)
    assert v == {"A02"}
    assert not rel.rejeitado
    assert "EST-0001" in rel.ocorrencias["A02"][0].chave


# ----------------------------------------------------------------- CLI e formatos de arquivo

def _gravar(tmp_path, doc, nome="envio.json"):
    p = tmp_path / nome
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return p


def test_cli_aceito_imprime_sha256(tmp_path, exemplo, capsys):
    p = _gravar(tmp_path, exemplo)
    assert validar_main([str(CONTRATO_MINIMO), str(p)]) == 0
    saida = capsys.readouterr().out
    assert hashlib.sha256(p.read_bytes()).hexdigest() in saida
    assert "RESULTADO: ACEITO" in saida


def test_cli_rejeitado_json_e_saida(tmp_path, exemplo, capsys):
    exemplo["envio"]["totais"]["estabelecimentos"] = 0
    p = _gravar(tmp_path, exemplo)
    rel_arq = tmp_path / "relatorio.json"
    assert validar_main([str(CONTRATO_MINIMO), str(p), "--json", "--saida", str(rel_arq)]) == 1
    rel = json.loads(capsys.readouterr().out)
    assert rel["situacao"] == "REJEITADO"
    r08 = next(r for r in rel["regras"] if r["regra"] == "R08")
    assert r08["ocorrencias"] == 1
    assert json.loads(rel_arq.read_text(encoding="utf-8"))["situacao"] == "REJEITADO"


def test_cli_erros_de_uso(tmp_path, exemplo, capsys):
    p = _gravar(tmp_path, exemplo)
    assert validar_main([str(CONTRATO_MINIMO), str(tmp_path / "nao_existe.json")]) == 2
    txt = _gravar(tmp_path, exemplo, "envio.txt")
    assert validar_main([str(CONTRATO_MINIMO), str(txt)]) == 2
    assert validar_main([str(tmp_path / "sem_contrato.yaml"), str(p)]) == 2
    assert validar_main([]) == 2


def test_json_malformado(tmp_path, capsys):
    p = tmp_path / "ruim.json"
    p.write_text('{"envio": ', encoding="utf-8")
    assert validar_main([str(CONTRATO_MINIMO), str(p)]) == 1
    assert "ARQ" in capsys.readouterr().out


def test_json_gz_e_zip(tmp_path, exemplo, capsys):
    bruto = json.dumps(exemplo).encode("utf-8")
    gz = tmp_path / "envio.json.gz"
    gz.write_bytes(gzip.compress(bruto))
    assert validar_main([str(CONTRATO_MINIMO), str(gz)]) == 0
    # zip em duas partes, com o mesmo cabeçalho
    parte1 = {**exemplo, "fiscalizacoes": exemplo["fiscalizacoes"][:1]}
    parte2 = {**exemplo, "estabelecimentos": [], "fiscalizacoes": exemplo["fiscalizacoes"][1:]}
    zp = tmp_path / "envio.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("parte1.json", json.dumps(parte1))
        z.writestr("parte2.json", json.dumps(parte2))
    assert validar_main([str(CONTRATO_MINIMO), str(zp)]) == 0
    assert "2 partes" in capsys.readouterr().out
