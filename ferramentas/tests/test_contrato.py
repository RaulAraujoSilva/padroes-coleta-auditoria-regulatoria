# -*- coding: utf-8 -*-
"""Validação do contrato: o mínimo é aceito; contratos com erro são recusados com mensagem clara."""
import copy

import pytest
import yaml

from conftest import CONTRATO_MINIMO
from contrato import (Condicao, ErroContrato, avaliar_expressao, carregar_contrato, cnpj_valido,
                      compilar_expressao, cpf_valido, validar_dados_contrato)


@pytest.fixture
def dados():
    return yaml.safe_load(CONTRATO_MINIMO.read_text(encoding="utf-8"))


def test_contrato_minimo_carrega(contrato):
    assert contrato.contrato == "fiscalizacao-teste"
    assert contrato.nomes_blocos == ["estabelecimentos", "fiscalizacoes"]
    assert [r.id for r in contrato.regras] == ["R06", "A01", "R09", "A02"]
    nomes_cab = [c.nome for c in contrato.cabecalho]
    assert nomes_cab[:8] == ["contrato", "versao_layout", "remetente", "cnpj_remetente", "data_referencia",
                             "tipo_carga", "data_referencia_anterior", "gerado_em"]
    assert "responsavel_envio" in nomes_cab
    assert contrato.campo_de("envio", "remetente").dominio == ["REGULADO_A", "REGULADO_B"]
    assert isinstance(contrato.campo_de("estabelecimentos", "motivo_baixa").obrigatorio, Condicao)
    assert contrato.campo_de("estabelecimentos", "data_abertura").exemplo == "2021-05-10"
    assert contrato.avisos == []


def _mexer(dados, func):
    d = copy.deepcopy(dados)
    func(d)
    return d


def _campo(d, bloco, nome):
    b = next(b for b in d["blocos"] if b["nome"] == bloco)
    return next(c for c in b["campos"] if c["nome"] == nome)


CASOS_INVALIDOS = {
    "enum sem dominio": (lambda d: _campo(d, "estabelecimentos", "situacao").pop("dominio"), "exige 'dominio'"),
    "tipo desconhecido": (lambda d: _campo(d, "estabelecimentos", "cnpj").update(tipo="documento"),
                          "tipo 'documento' desconhecido"),
    "referencia a bloco inexistente": (
        lambda d: _campo(d, "fiscalizacoes", "id_estabelecimento").update(referencia="lojas.id"),
        "cita o bloco lojas"),
    "referencia a campo inexistente": (
        lambda d: _campo(d, "fiscalizacoes", "id_estabelecimento").update(referencia="estabelecimentos.codigo"),
        "cita o campo codigo"),
    "chave inexistente": (lambda d: d["blocos"][0].update(chave=["codigo"]), "campo de chave codigo"),
    "id reservado": (lambda d: d["regras"][0].update(id="R03"), "reservado"),
    "id repetido": (lambda d: d["regras"][1].update(id="R06", severidade="rejeicao"), "repetido"),
    "id fora do padrao": (lambda d: d["regras"][0].update(id="X1"), "id 'X1' inválido"),
    "condicao com campo inexistente": (
        lambda d: _campo(d, "estabelecimentos", "motivo_baixa").update(obrigatorio={"se": "status", "igual": "X"}),
        "cita o campo status"),
    "condicao com valor fora do dominio": (
        lambda d: _campo(d, "estabelecimentos", "motivo_baixa").update(
            obrigatorio={"se": "situacao", "igual": "CANCELADO"}),
        "não pertence ao domínio"),
    "condicao sem operador": (
        lambda d: _campo(d, "estabelecimentos", "motivo_baixa").update(obrigatorio={"se": "situacao"}),
        "exatamente um operador"),
    "expressao insegura": (lambda d: d["regras"][3].update(condicao="().__class__"), "não permitido"),
    "expressao com nome desconhecido": (lambda d: d["regras"][3].update(condicao="open('x')"),
                                        "nome desconhecido"),
    "expressao com sintaxe invalida": (lambda d: d["regras"][3].update(condicao="r['a'] =="), "sintaxe"),
    "ordem_datas com campo nao data": (lambda d: d["regras"][0].update(antes="resultado"), "deve ser do tipo"),
    "data_minima com valor invalido": (lambda d: d["regras"][1].update(valor="01/01/2020"), "AAAA-MM-DD"),
    "regra em bloco inexistente": (lambda d: d["regras"][0].update(bloco="lojas"), "bloco 'lojas' não existe"),
    "versao numerica": (lambda d: d.update(versao=1.0), "entre aspas"),
    "nome de contrato invalido": (lambda d: d.update(contrato="Meu Contrato"), "'contrato' ausente ou inválido"),
    "exemplo fora do formato": (lambda d: _campo(d, "estabelecimentos", "id_estabelecimento").update(exemplo="X1"),
                                "exemplo 'X1' inválido"),
    "cnpj de exemplo invalido": (lambda d: _campo(d, "estabelecimentos", "cnpj").update(exemplo="11222333000182"),
                                 "dígito verificador"),
    "campo repetido": (lambda d: d["blocos"][0]["campos"].append(dict(d["blocos"][0]["campos"][0])),
                       "mais de uma vez"),
    "evento em campo nao data": (lambda d: _campo(d, "estabelecimentos", "situacao").update(evento=True),
                                 "evento: true"),
    "cabecalho com nome reservado": (lambda d: d["cabecalho"][0].update(nome="remetente"), "reservado"),
    "bloco reservado": (lambda d: d["blocos"][0].update(nome="envio"), "reservado"),
    "sem blocos": (lambda d: d.update(blocos=[]), "'blocos' deve ser uma lista não vazia"),
    "regex invalida": (lambda d: _campo(d, "estabelecimentos", "id_estabelecimento").update(formato="(["),
                       "expressão regular inválida"),
}


@pytest.mark.parametrize("caso", list(CASOS_INVALIDOS))
def test_contrato_invalido_e_recusado(dados, caso):
    mexer, trecho = CASOS_INVALIDOS[caso]
    with pytest.raises(ErroContrato) as info:
        validar_dados_contrato(_mexer(dados, mexer), "teste.yaml")
    assert trecho in str(info.value), str(info.value)


def test_varios_erros_reportados_juntos(dados):
    def mexer(d):
        d["regras"][0]["id"] = "R01"
        _campo(d, "estabelecimentos", "situacao").pop("dominio")
    with pytest.raises(ErroContrato) as info:
        validar_dados_contrato(_mexer(dados, mexer))
    assert len(info.value.erros) >= 2


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroContrato, match="não encontrado"):
        carregar_contrato(tmp_path / "nao_existe.yaml")


def test_yaml_malformado(tmp_path):
    p = tmp_path / "ruim.yaml"
    p.write_text("contrato: [aberto\n", encoding="utf-8")
    with pytest.raises(ErroContrato, match="YAML malformado"):
        carregar_contrato(p)


def test_chave_desconhecida_vira_aviso(dados):
    d = _mexer(dados, lambda d: _campo(d, "estabelecimentos", "cnpj").update(observacao="x"))
    c = validar_dados_contrato(d)
    assert any("observacao" in a for a in c.avisos)


def test_expressao_com_gerador_enxerga_r_e_e():
    codigo = compilar_expressao("any(i.get('x') == r['x'] for i in e['itens'])")
    assert avaliar_expressao(codigo, {"x": 1}, {"itens": [{"x": 2}, {"x": 1}]}) is True
    assert avaliar_expressao(codigo, {"x": 3}, {"itens": [{"x": 2}]}) is False


def test_expressao_sem_builtins_perigosos():
    with pytest.raises(ValueError):
        compilar_expressao("__import__('os')")
    with pytest.raises(ValueError):
        compilar_expressao("(lambda: 1)()")


def test_digitos_verificadores():
    assert cnpj_valido("11222333000181")
    assert not cnpj_valido("11222333000182")
    assert not cnpj_valido("11111111111111")
    assert cpf_valido("52998224725")
    assert not cpf_valido("52998224726")
