# -*- coding: utf-8 -*-
"""Testes do verificador.

Rodar a partir da raiz do repositório:  python -m pytest exemplos/ipg-gas-rj -q
(ou, dentro desta pasta:  python test_autovistoria.py)
"""
import json
import re
from datetime import date
from pathlib import Path

from autovistoria import Verificador, ler_csv, rodar as rodar_pasta, somar_anos

AQUI = Path(__file__).parent
BASE = date(2026, 11, 10)


def rodar(**ajustes):
    p = json.loads((AQUI / "parametros.json").read_text(encoding="utf-8"))
    p.update(ajustes)
    ex = AQUI / "exemplo"
    v = Verificador(p, ler_csv(ex / "habilitacoes.csv"), ler_csv(AQUI / "dados" / "cronograma_ipg.csv"))
    insp = {}
    for i in ler_csv(ex / "inspecoes.csv"):
        insp.setdefault(i["id_unidade"], []).append(i)
    return {u["id_unidade"]: v.avaliar(u, insp.get(u["id_unidade"], []), BASE) for u in ler_csv(ex / "unidades.csv")}


def test_status_padrao():
    r = rodar()
    esperado = {
        "U01": "EM_DIA", "U02": "PRIMEIRA_NAO_REALIZADA", "U03": "VENCIDA", "U04": "EM_DIA",
        "U05": "PRIMEIRA_NAO_REALIZADA", "U06": "REPROVADA", "U07": "ADEQUACAO_VENCIDA",
        "U08": "FORA_DO_ESCOPO", "U09": "PRIMEIRA_PENDENTE_NO_PRAZO", "U10": "PRIMEIRA_NAO_REALIZADA",
        "U11": "EM_DIA", "U12": "PRIMEIRA_NAO_REALIZADA", "U13": "FORA_DO_ESCOPO",
    }
    assert {k: v.status for k, v in r.items()} == esperado
    assert r["U06"].obrigacao_concessionaria == "NAO_INTERROMPEU"
    assert r["U03"].data_limite == date(2024, 6, 1)


def test_cronograma_regra_x_tabela():
    assert rodar()["U02"].data_limite == date(2026, 3, 22)                                # Madureira, tabela
    assert rodar(cronograma_prevalece="regra")["U02"].data_limite == date(2026, 9, 23)    # Madureira, regra
    assert "L6" in rodar()["U02"].lacunas_acionadas


def test_oia_pos_in113_so_legado():
    assert rodar(oia_inmetro_apos_in113="so_legado")["U11"].status == "PRIMEIRA_NAO_REALIZADA"
    assert "L1" in rodar()["U11"].lacunas_acionadas


def test_credenciamento_cruzado():
    assert rodar(credenciamento_vale_para_outra_concessionaria=True)["U10"].status == "EM_DIA"


def test_in113_interrupcao_discricionaria():
    r = rodar(interrupcao_obrigatoria_apos_reprovacao=False)
    assert r["U06"].obrigacao_concessionaria == "VERIFICAR_AVALIACAO_DE_INTERRUPCAO"


def test_unidade_desligada_no_escopo():
    assert rodar(incluir_unidades_sem_fornecimento=True)["U13"].status == "PRIMEIRA_NAO_REALIZADA"


def test_29_de_fevereiro():
    assert somar_anos(date(2024, 2, 29), 5, "aniversario") == date(2029, 2, 28)


# ---------------------------------------------------------------- dados fictícios

def cnpj_valido(doc: str) -> bool:
    n = re.sub(r"\D", "", doc)
    if len(n) != 14 or len(set(n)) == 1:
        return False
    def dv(base):
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2][-len(base):]
        r = sum(int(a) * b for a, b in zip(base, pesos)) % 11
        return "0" if r < 2 else str(11 - r)
    return n[12] == dv(n[:12]) and n[13] == dv(n[:13])


def test_exemplo_usa_cnpjs_ficticios_com_digito_valido():
    ex = AQUI / "exemplo"
    docs = [h["doc_inspetora"] for h in ler_csv(ex / "habilitacoes.csv")]
    docs += [i["doc_inspetora"] for i in ler_csv(ex / "inspecoes.csv")]
    assert docs and all(cnpj_valido(doc) for doc in docs)


# ---------------------------------------------------------------- versão didática (P1–P8)

def test_regra_didatica():
    from regra_autovistoria import Habilitacao, Inspecao, Parametros, RegraAutovistoria, Unidade
    hab = [Habilitacao("90.123.456/0001-31", "OIA_INMETRO", date(2016, 10, 5)),
           Habilitacao("44.555.666/0001-81", "CREDENCIADA_CEG", date(2024, 2, 1)),
           Habilitacao("99.887.766/0001-05", "OIA_INMETRO", date(2024, 3, 10))]
    cron = {("RIO DE JANEIRO", "MADUREIRA"): {"tabela": date(2026, 3, 22), "regra": date(2026, 9, 23)}}
    u_mad = Unidade("U2", "CEG", "RIO DE JANEIRO", "MADUREIRA", "RESIDENCIAL", True)
    u_ipa = Unidade("U6", "CEG", "RIO DE JANEIRO", "IPANEMA", "RESIDENCIAL", True)
    i_pos = [Inspecao("I6", date(2024, 5, 1), "99.887.766/0001-05", "APROVADO", "CREA-RJ 777")]
    u_nit = Unidade("U4", "CEG", "NITEROI", "*", "RESIDENCIAL", True)
    i_rep = [Inspecao("I4", date(2026, 1, 15), "44.555.666/0001-81", "REPROVADO", "CREA-RJ 123")]

    padrao = RegraAutovistoria(Parametros(), hab, cron)
    assert padrao.avaliar(u_mad, [], BASE)["data_limite"] == date(2026, 3, 22)
    assert padrao.avaliar(u_ipa, i_pos, BASE)["status"] == "CONFORME"
    assert padrao.avaliar(u_nit, i_rep, BASE)["concessionaria"] == "NAO_INTERROMPEU"

    alt = RegraAutovistoria(Parametros(p1_oia_pos_in113_vale=False, p6_cronograma="regra",
                                       p8_interrupcao_obrigatoria=False), hab, cron)
    assert alt.avaliar(u_mad, [], BASE)["data_limite"] == date(2026, 9, 23)          # P6
    assert alt.avaliar(u_ipa, i_pos, BASE)["status"] == "PRIMEIRA_NAO_REALIZADA"  # P1
    assert alt.avaliar(u_nit, i_rep, BASE)["concessionaria"] == "VERIFICAR_AVALIACAO_DE_INTERRUPCAO"  # P8


# ---------------------------------------------------------------- versão "só o texto"

def test_exercicio_tres_saidas():
    from exercicio_autovistoria import CONFORME, DELIBERAR, NAO_CONFORME, verificar_autovistoria
    inmetro = {"22.334.455/0001-86": [(date(2016, 1, 1), None)],
               "44.555.666/0001-81": [(date(2018, 1, 1), date(2022, 12, 31))]}
    def v(dt, doc):
        return verificar_autovistoria(BASE, True, dt, doc, inmetro)[0]
    assert v(date(2023, 5, 10), "22.334.455/0001-86") == CONFORME
    assert v(date(2019, 6, 1), "22.334.455/0001-86") == NAO_CONFORME
    assert v(date(2022, 3, 1), "44.555.666/0001-81") == DELIBERAR
    assert verificar_autovistoria(BASE, None, None, None, inmetro)[0] == DELIBERAR


# ---------------------------------------------------------------- do envio ao veredito

def test_envio_completo_no_verificador(tmp_path):
    from json_para_verificador import converter
    envio = json.loads((AQUI.parent / "envios" / "exemplo_envio_completo.json").read_text(encoding="utf-8"))
    converter(envio, tmp_path)
    res = rodar_pasta(tmp_path, date(2026, 10, 31), AQUI / "parametros.json", AQUI / "dados" / "cronograma_ipg.csv")
    assert {r.id_unidade: r.status for r in res} == {
        "1000234567": "EM_DIA", "1000234568": "VENCIDA", "1000876540": "PRIMEIRA_NAO_REALIZADA",
        "1000555001": "FORA_DO_ESCOPO", "1000666002": "EM_DIA", "1000777003": "FORA_DO_ESCOPO",
        "2000100200": "VENCIDA",
    }


if __name__ == "__main__":
    import inspect
    import tempfile
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            if "tmp_path" in inspect.signature(f).parameters:
                with tempfile.TemporaryDirectory() as t:
                    f(Path(t))
            else:
                f()
            print("ok", nome)
