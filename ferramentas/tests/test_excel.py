# -*- coding: utf-8 -*-
"""Ida e volta pelo Excel: preencher o modelo gerado com o exemplo e validar."""
import json
from datetime import date

import pytest
from openpyxl import load_workbook

from conftest import CONTRATO_MINIMO
from gerador_excel import gerar_excel
from validar_envio import main as validar_main, validar_arquivo


def preencher(contrato, modelo, doc, destino):
    """Preenche a planilha-modelo com o documento JSON, como faria um regulado."""
    wb = load_workbook(modelo)
    env = wb["envio"]
    linhas = {env.cell(row=i, column=1).value: i for i in range(2, env.max_row + 1)}
    for c in contrato.cabecalho:
        if c.nome in doc["envio"]:
            env.cell(row=linhas[c.nome], column=2, value=_para_celula(c, doc["envio"][c.nome]))
    for bloco, total in doc["envio"]["totais"].items():
        env.cell(row=linhas[f"totais.{bloco}"], column=2, value=total)
    for b in contrato.blocos:
        ws = wb[b.nome]
        for i, reg in enumerate(doc[b.nome], start=2):
            for col, c in enumerate(b.campos, start=1):
                if c.nome in reg:
                    ws.cell(row=i, column=col, value=_para_celula(c, reg[c.nome]))
    wb.save(destino)
    return destino


def _para_celula(c, v):
    if c.tipo == "booleano":
        return "SIM" if v else "NAO"
    if c.tipo == "data":
        return date.fromisoformat(v)
    return v


@pytest.fixture
def modelo(contrato, tmp_path):
    return gerar_excel(contrato, tmp_path / "modelo.xlsx")


def test_ida_e_volta_excel(contrato, exemplo, modelo, tmp_path):
    xlsx = preencher(contrato, modelo, exemplo, tmp_path / "preenchido.xlsx")
    rel, doc = validar_arquivo(contrato, xlsx)
    assert rel.situacao == "ACEITO", rel.como_texto()
    assert doc == exemplo


def test_exportar_json(contrato, exemplo, modelo, tmp_path, capsys):
    xlsx = preencher(contrato, modelo, exemplo, tmp_path / "preenchido.xlsx")
    saida = tmp_path / "convertido.json"
    assert validar_main([str(CONTRATO_MINIMO), str(xlsx), "--exportar-json", str(saida)]) == 0
    assert json.loads(saida.read_text(encoding="utf-8")) == exemplo


def test_excel_avisos_e_celula_no_relatorio(contrato, exemplo, modelo, tmp_path):
    xlsx = preencher(contrato, modelo, exemplo, tmp_path / "preenchido.xlsx")
    wb = load_workbook(xlsx)
    ws = wb["fiscalizacoes"]
    cab = [c.value for c in ws[1]]
    ws.cell(row=2, column=cab.index("data_relatorio") + 1, value="N/A")          # aviso, omitido
    ws.cell(row=3, column=cab.index("prazo_dias") + 1, value="=10+5")            # fórmula sem valor calculado
    ws.cell(row=4, column=cab.index("resultado") + 1, value="MULTADO")           # fora do domínio
    est = wb["estabelecimentos"]
    cab_e = [c.value for c in est[1]]
    est.cell(row=2, column=cab_e.index("cnpj") + 1, value="11.222.333/0001-81")  # pontuação removida
    env = wb["envio"]
    for i in range(2, env.max_row + 1):
        if env.cell(row=i, column=1).value in ("gerado_em", "totais.fiscalizacoes"):
            env.cell(row=i, column=2).value = None                                 # preenchidos pela ferramenta
    wb.save(xlsx)

    rel, doc = validar_arquivo(contrato, xlsx)
    avisos = "\n".join(rel.avisos_conversao)
    assert "'N/A' tratado como vazio" in avisos
    assert "fórmula sem valor calculado" in avisos
    assert "pontuação removida" in avisos
    assert "gerado_em vazio" in avisos and "totais.fiscalizacoes vazio" in avisos
    assert "data_relatorio" not in doc["fiscalizacoes"][0]
    assert doc["estabelecimentos"][0]["cnpj"] == "11222333000181"
    assert rel.rejeitado
    r01 = rel.ocorrencias["R01"]
    assert any(o.campo == "resultado" and o.celula and o.celula.startswith("fiscalizacoes!") for o in r01)
    assert "R09" in {r for r, lst in rel.ocorrencias.items() if lst}   # prazo_dias omitido com AUTUADO


def test_excel_sem_aba_envio(contrato, tmp_path, capsys):
    from openpyxl import Workbook
    p = tmp_path / "qualquer.xlsx"
    Workbook().save(p)
    assert validar_main([str(CONTRATO_MINIMO), str(p)]) == 1
    assert "aba 'envio'" in capsys.readouterr().out
