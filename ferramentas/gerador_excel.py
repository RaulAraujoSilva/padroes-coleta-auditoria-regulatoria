# -*- coding: utf-8 -*-
"""
Gera a planilha-modelo (canal Excel) a partir do contrato de coleta.

Abas:
  LEIA-ME      instruções de preenchimento, legenda de cores e o teste de auditoria
  envio        cabeçalho no formato campo/valor, inclusive as linhas totais.<bloco>
  <bloco>      uma aba por bloco, formatada como Tabela do Excel, cabeçalho = nomes dos campos
  dicionario   todos os campos, com tipo, obrigatoriedade, domínio/formato, descrição e origem
  listas       (oculta) valores das listas suspensas

Cabeçalhos coloridos por obrigatoriedade (azul = obrigatório, laranja = condicional,
cinza = opcional), com nota explicativa; validação de dados por tipo; painéis congelados.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo

from contrato import Campo, Contrato

LINHAS_FORMATADAS = 500          # linhas com formato de célula pré-aplicado em cada aba de bloco
ULTIMA_LINHA = 1_048_576
COR = {"obrigatorio": "1F4E79", "condicional": "C55A11", "opcional": "7F7F7F"}
FONTE_CAB = Font(name="Calibri", bold=True, color="FFFFFF")
FMT_DATA = "yyyy-mm-dd"
FMT_TEXTO = "@"


def _categoria(c: Campo) -> str:
    if c.obrigatorio is True:
        return "obrigatorio"
    return "condicional" if c.condicional else "opcional"


def _preenchimento(c: Campo) -> PatternFill:
    return PatternFill("solid", fgColor=COR[_categoria(c)])


def _nota(c: Campo, autor: str) -> Comment:
    linhas = [c.descricao or c.nome, f"Tipo: {c.tipo}", f"Obrigatório: {c.texto_obrigatorio()}",
              f"Domínio/formato: {c.texto_dominio()}"]
    if c.origem:
        linhas.append(f"Quem detém: {c.origem}")
    com = Comment("\n".join(linhas), autor or "padrão de coleta")
    com.width, com.height = 340, 160
    return com


def _formato_celula(c: Campo) -> str | None:
    if c.tipo == "data":
        return FMT_DATA
    if c.tipo == "inteiro":
        return "0"
    if c.tipo == "decimal":
        return "General"
    if c.tipo == "booleano":
        return None
    return FMT_TEXTO


def _criar_listas(wb: Workbook, contrato: Contrato) -> dict[str, str]:
    """Aba oculta com uma coluna por domínio. Devolve {chave: referência absoluta}."""
    ws = wb.create_sheet("listas")
    dominios: dict[str, list[str]] = {"SIM_NAO": ["SIM", "NAO"]}
    for c in contrato.cabecalho:
        if c.tipo == "enum":
            dominios[f"envio.{c.nome}"] = c.dominio or []
    for b in contrato.blocos:
        for c in b.campos:
            if c.tipo == "enum":
                dominios[f"{b.nome}.{c.nome}"] = c.dominio or []
    refs = {}
    for col, (chave, valores) in enumerate(dominios.items(), start=1):
        letra = get_column_letter(col)
        ws.cell(row=1, column=col, value=chave).font = Font(bold=True)
        for i, v in enumerate(valores, start=2):
            ws.cell(row=i, column=col, value=v).number_format = FMT_TEXTO
        refs[chave] = f"listas!${letra}$2:${letra}${len(valores) + 1}"
        ws.column_dimensions[letra].width = max([len(chave)] + [len(v) for v in valores]) + 2
    ws.sheet_state = "hidden"
    return refs


def _validacao(c: Campo, chave_lista: str, primeira: str, refs: dict[str, str]) -> DataValidation | None:
    dv = None
    t = c.tipo
    if t == "enum":
        dv = DataValidation(type="list", formula1=refs[chave_lista], allow_blank=True)
        dv.error = "Escolha um valor da lista: " + ", ".join(c.dominio or [])
    elif t == "booleano":
        dv = DataValidation(type="list", formula1=refs["SIM_NAO"], allow_blank=True)
        dv.error = "Escolha SIM ou NAO."
    elif t == "data":
        dv = DataValidation(type="date", operator="between", allow_blank=True,
                            formula1="DATE(1900,1,1)", formula2="DATE(2099,12,31)")
        dv.error = "Informe uma data válida (célula de data, exibida como AAAA-MM-DD)."
    elif t in ("cnpj", "cpf", "cep", "ibge_municipio", "sha256"):
        n = {"cnpj": 14, "cpf": 11, "cep": 8, "ibge_municipio": 7, "sha256": 64}[t]
        dv = DataValidation(type="textLength", operator="equal", formula1=str(n), allow_blank=True)
        dv.error = f"Informe {n} caracteres, sem pontos, barras, traços ou espaços (célula de texto)."
    elif t == "cpf_cnpj":
        dv = DataValidation(type="custom", allow_blank=True,
                            formula1=f"OR(LEN({primeira})=11,LEN({primeira})=14)")
        dv.error = "CPF (11 dígitos) ou CNPJ (14 dígitos), só números."
    elif t == "inteiro":
        mn = c.minimo if c.minimo is not None else -2147483648
        mx = c.maximo if c.maximo is not None else 2147483647
        dv = DataValidation(type="whole", operator="between", formula1=str(int(mn)), formula2=str(int(mx)),
                            allow_blank=True)
        dv.error = f"Número inteiro entre {mn} e {mx}."
    elif t == "decimal" and (c.minimo is not None or c.maximo is not None):
        mn = c.minimo if c.minimo is not None else -1e15
        mx = c.maximo if c.maximo is not None else 1e15
        dv = DataValidation(type="decimal", operator="between", formula1=str(mn), formula2=str(mx),
                            allow_blank=True)
        dv.error = f"Número entre {mn} e {mx}."
    elif t == "texto" and c.tamanho_max:
        dv = DataValidation(type="textLength", operator="lessThanOrEqual", formula1=str(c.tamanho_max),
                            allow_blank=True)
        dv.error = f"No máximo {c.tamanho_max} caracteres."
    if dv is not None:
        dv.errorTitle = f"Valor inválido em {c.nome}"
        dv.errorStyle = "stop"
        dv.showErrorMessage = True
    return dv


def _leia_me(wb: Workbook, contrato: Contrato) -> None:
    ws = wb.active
    ws.title = "LEIA-ME"
    ta = contrato.teste_auditoria or {}
    linhas: list[tuple[str, str]] = [
        ("titulo", f"{contrato.titulo} — modelo de envio, layout {contrato.versao}"),
        ("", ""),
        ("Contrato", f"{contrato.contrato} (versão {contrato.versao})"),
        ("Órgão", contrato.orgao),
        ("Finalidade", contrato.descricao),
        ("Remetentes", ", ".join(contrato.regulados)),
    ]
    p = contrato.periodicidade or {}
    if p:
        linhas.append(("Periodicidade", f"{p.get('regular', '')}; prazo: {p.get('prazo_entrega', '')}; "
                                        f"carga inicial: {p.get('carga_inicial', '')}"))
    if ta.get("pergunta"):
        linhas.append(("Teste de auditoria", str(ta["pergunta"]).strip()))
    linhas += [
        ("", ""),
        ("secao", "Como preencher"),
        ("1", "Preencha a aba 'envio' (coluna 'valor') e uma linha por registro em cada aba de bloco."),
        ("2", "Não altere os nomes das abas nem os cabeçalhos das colunas; não insira colunas no meio."),
        ("3", "Deixe a célula vazia quando não houver informação. Não use '-', 'N/A' ou textos equivalentes."),
        ("4", "Datas em células de data (exibidas como AAAA-MM-DD). Data e hora como texto com fuso, "
              "ex.: 2026-01-31T18:00:00-03:00."),
        ("5", "CNPJ, CPF, CEP e código IBGE só com dígitos, em células de texto (preserva zeros à esquerda)."),
        ("6", "Campos SIM/NAO e de domínio: escolha na lista suspensa."),
        ("7", "Cole dados como valores (sem fórmulas)."),
        ("8", "As linhas totais.<bloco> da aba 'envio' informam quantos registros há em cada aba; "
              "a coluna 'conferencia' mostra a contagem calculada."),
        ("9", "Antes de entregar, rode: python ferramentas/validar_envio.py contrato.yaml esta_planilha.xlsx"),
        ("", ""),
        ("secao", "Legenda das cores do cabeçalho"),
        ("obrigatorio", "Azul-escuro: obrigatório"),
        ("condicional", "Laranja: obrigatório em certas condições (veja a nota da célula)"),
        ("opcional", "Cinza: opcional"),
        ("", ""),
        ("secao", "Abas"),
        ("envio", "Cabeçalho do envio (campo/valor) e totais"),
    ]
    for b in contrato.blocos:
        linhas.append((b.nome, b.descricao))
    linhas += [("dicionario", "Descrição de todos os campos"), ("listas", "(oculta) valores das listas")]

    for i, (a, b) in enumerate(linhas, start=1):
        if a == "titulo":
            ws.cell(row=i, column=1, value=b).font = Font(bold=True, size=14)
            continue
        if a == "secao":
            ws.cell(row=i, column=1, value=b).font = Font(bold=True, size=12)
            continue
        ca = ws.cell(row=i, column=1, value=a or None)
        cb = ws.cell(row=i, column=2, value=b or None)
        cb.alignment = Alignment(wrap_text=True, vertical="top")
        ca.alignment = Alignment(vertical="top")
        if a in COR:
            ca.fill = PatternFill("solid", fgColor=COR[a])
            ca.font = FONTE_CAB
        else:
            ca.font = Font(bold=True)
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 110


def _aba_envio(wb: Workbook, contrato: Contrato, refs: dict[str, str]) -> None:
    ws = wb.create_sheet("envio")
    cab = ["campo", "valor", "obrigatorio", "tipo", "dominio_formato", "descricao", "conferencia"]
    for col, t in enumerate(cab, start=1):
        cel = ws.cell(row=1, column=col, value=t)
        cel.font = FONTE_CAB
        cel.fill = PatternFill("solid", fgColor="404040")
    ws["B1"].comment = Comment("Preencha só a coluna 'valor'. As demais colunas são informativas.",
                               contrato.orgao or "padrão de coleta")
    ws["G1"].comment = Comment("Contagem calculada pelo Excel, só para conferência visual. Não é enviada.",
                               contrato.orgao or "padrão de coleta")
    linha = 2
    for c in contrato.cabecalho:
        a = ws.cell(row=linha, column=1, value=c.nome)
        a.font = FONTE_CAB
        a.fill = _preenchimento(c)
        a.comment = _nota(c, contrato.orgao)
        v = ws.cell(row=linha, column=2)
        fmt = _formato_celula(c)
        if fmt:
            v.number_format = fmt
        if c.constante is not None:
            v.value = c.constante
        ws.cell(row=linha, column=3, value=c.texto_obrigatorio())
        ws.cell(row=linha, column=4, value=c.tipo)
        ws.cell(row=linha, column=5, value=c.texto_dominio())
        ws.cell(row=linha, column=6, value=c.descricao).alignment = Alignment(wrap_text=True)
        dv = _validacao(c, f"envio.{c.nome}", f"B{linha}", refs)
        if dv is not None:
            ws.add_data_validation(dv)
            dv.add(f"B{linha}")
        linha += 1
    for b in contrato.blocos:
        a = ws.cell(row=linha, column=1, value=f"totais.{b.nome}")
        a.font = FONTE_CAB
        a.fill = PatternFill("solid", fgColor=COR["obrigatorio"])
        v = ws.cell(row=linha, column=2)
        v.number_format = "0"
        ws.cell(row=linha, column=3, value="Sim")
        ws.cell(row=linha, column=4, value="inteiro")
        ws.cell(row=linha, column=5, value="número inteiro ≥ 0")
        ws.cell(row=linha, column=6, value=f"Quantidade de registros na aba {b.nome} (regra R08).")
        primeira = b.campo(b.chave[0]) if b.chave else b.campos[0]
        letra = get_column_letter(b.campos.index(primeira) + 1)
        f = ws.cell(row=linha, column=7, value=f"=MAX(COUNTA('{b.nome}'!{letra}:{letra})-1,0)")
        f.font = Font(italic=True, color="595959")
        dv = DataValidation(type="whole", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
        dv.error, dv.errorTitle, dv.showErrorMessage = "Número inteiro ≥ 0.", "Valor inválido", True
        ws.add_data_validation(dv)
        dv.add(f"B{linha}")
        linha += 1
    for letra, larg in zip("ABCDEFG", (30, 40, 26, 12, 44, 70, 14)):
        ws.column_dimensions[letra].width = larg
    ws.freeze_panes = "B2"


def _aba_bloco(wb: Workbook, contrato: Contrato, b, refs: dict[str, str]) -> None:
    ws = wb.create_sheet(b.nome)
    for col, c in enumerate(b.campos, start=1):
        cel = ws.cell(row=1, column=col, value=c.nome)
        cel.font = FONTE_CAB
        cel.fill = _preenchimento(c)
        cel.alignment = Alignment(vertical="center")
        cel.comment = _nota(c, contrato.orgao)
        letra = get_column_letter(col)
        ws.column_dimensions[letra].width = max(14, min(40, len(c.nome) + 4))
        fmt = _formato_celula(c)
        if fmt:
            for linha in range(2, LINHAS_FORMATADAS + 2):
                ws.cell(row=linha, column=col).number_format = fmt
        dv = _validacao(c, f"{b.nome}.{c.nome}", f"{letra}2", refs)
        if dv is not None:
            ws.add_data_validation(dv)
            dv.add(f"{letra}2:{letra}{ULTIMA_LINHA}")
    ultima = get_column_letter(len(b.campos))
    tabela = Table(displayName=f"tbl_{b.nome}", ref=f"A1:{ultima}2")
    tabela.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
    ws.add_table(tabela)
    ws.freeze_panes = "A2"


def _aba_dicionario(wb: Workbook, contrato: Contrato) -> None:
    ws = wb.create_sheet("dicionario")
    cab = ["bloco", "campo", "tipo", "obrigatorio", "dominio_formato", "descricao", "origem"]
    for col, t in enumerate(cab, start=1):
        cel = ws.cell(row=1, column=col, value=t)
        cel.font = FONTE_CAB
        cel.fill = PatternFill("solid", fgColor="404040")
    linha = 2
    grupos = [("envio", contrato.cabecalho)] + [(b.nome, b.campos) for b in contrato.blocos]
    for bloco, campos in grupos:
        for c in campos:
            valores = [bloco, c.nome, c.tipo, c.texto_obrigatorio(), c.texto_dominio(), c.descricao, c.origem]
            for col, v in enumerate(valores, start=1):
                cel = ws.cell(row=linha, column=col, value=v)
                cel.alignment = Alignment(wrap_text=True, vertical="top")
            linha += 1
    for letra, larg in zip("ABCDEFG", (22, 28, 12, 28, 44, 70, 30)):
        ws.column_dimensions[letra].width = larg
    tabela = Table(displayName="tbl_dicionario", ref=f"A1:G{max(linha - 1, 2)}")
    tabela.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
    ws.add_table(tabela)
    ws.freeze_panes = "C2"


def gerar_excel(contrato: Contrato, destino: Path) -> Path:
    """Gera a planilha-modelo vazia e devolve o caminho gravado."""
    wb = Workbook()
    _leia_me(wb, contrato)
    refs = _criar_listas(wb, contrato)
    _aba_envio(wb, contrato, refs)
    for b in contrato.blocos:
        _aba_bloco(wb, contrato, b, refs)
    _aba_dicionario(wb, contrato)
    # ordem: LEIA-ME, envio, blocos, dicionario, listas (oculta por último)
    listas = wb["listas"]
    wb.move_sheet(listas, offset=len(wb.sheetnames) - 1 - wb.sheetnames.index("listas"))
    wb.active = 0
    destino.parent.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return destino


def nome_arquivo_excel(contrato: Contrato) -> str:
    return f"modelo_{contrato.contrato}_v{contrato.versao}.xlsx"
