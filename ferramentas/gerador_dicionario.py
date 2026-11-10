# -*- coding: utf-8 -*-
"""Gera o dicionário de dados em Markdown a partir do contrato de coleta."""
from __future__ import annotations

from contrato import REGRAS_AUTOMATICAS, Campo, Contrato


def _cel(v) -> str:
    """Escapa o texto para uma célula de tabela Markdown."""
    s = "" if v is None else str(v)
    return " ".join(s.split()).replace("|", "\\|")


def _tabela_campos(campos: list[Campo]) -> list[str]:
    l = ["| Campo | Tipo | Obrigatório | Domínio / formato | Descrição | Origem (quem detém) |",
         "|---|---|---|---|---|---|"]
    for c in campos:
        l.append(f"| `{c.nome}` | {c.tipo} | {_cel(c.texto_obrigatorio())} | {_cel(c.texto_dominio())} | "
                 f"{_cel(c.descricao)} | {_cel(c.origem)} |")
    return l


def _descricao_regra(r) -> str:
    if r.tipo == "ordem_datas":
        return f"`{r.depois}` ≥ `{r.antes}`"
    if r.tipo == "data_minima":
        return f"`{r.campo}` ≥ {r.valor}"
    if r.tipo == "condicional":
        return f"se {r.se.texto()}, então {r.entao.texto()}"
    return f"`{r.condicao}`"


def gerar_dicionario(contrato: Contrato) -> str:
    c = contrato
    ta = c.teste_auditoria or {}
    l: list[str] = [f"# Dicionário de dados — {c.titulo}", ""]
    l.append(f"Contrato de coleta `{c.contrato}`, versão do layout **{c.versao}**"
             + (f", definido por {c.orgao}" if c.orgao else "") + ".")
    l.append("")
    if c.descricao:
        l += [c.descricao.strip(), ""]
    l.append(f"**Remetentes:** {', '.join(c.regulados)}.")
    p = c.periodicidade or {}
    if p:
        partes = []
        if p.get("regular"):
            partes.append(f"periodicidade {p['regular']}")
        if p.get("prazo_entrega"):
            partes.append(f"prazo: {p['prazo_entrega']}")
        if p.get("carga_inicial"):
            partes.append(f"carga inicial: {p['carga_inicial']}")
        l += ["", "**Periodicidade:** " + "; ".join(partes) + "."]
    l.append("")
    l.append("> Gerado automaticamente por `ferramentas/gerar_padrao.py` a partir do `contrato.yaml`. "
             "Não edite à mão: altere o contrato e gere de novo.")
    l.append("")

    if ta or c.base_normativa:
        l += ["## Teste de auditoria", ""]
        if ta.get("pergunta"):
            l += [f"**Pergunta:** {' '.join(str(ta['pergunta']).split())}", ""]
        if ta.get("regra"):
            l += ["**Regra:**", "", "```text", str(ta["regra"]).rstrip(), "```", ""]
        if ta.get("classificacao"):
            l += [f"**Classificação:** {ta['classificacao']}", ""]
        if ta.get("saidas"):
            l += [f"**Saídas possíveis:** {', '.join(map(str, ta['saidas']))}", ""]
        if c.base_normativa:
            l += ["**Base normativa:**", ""]
            for b in c.base_normativa:
                url = f" — <{b['url']}>" if b.get("url") else ""
                l.append(f"- `{b.get('id')}`: {b.get('descricao')}{url}")
            l.append("")
        if c.lacunas:
            l += ["### Lacunas", "",
                  "| Id | Trecho | Problema | Decisão padrão | Quem decide |", "|---|---|---|---|---|"]
            for x in c.lacunas:
                l.append(f"| {_cel(x.id)} | {_cel(x.trecho)} | {_cel(x.problema)} | "
                         f"{_cel(x.decisao_padrao)} | {_cel(x.quem_decide)} |")
            l.append("")

    l += ["## Estrutura do envio", "",
          "O envio é um objeto JSON com o cabeçalho `envio` e uma lista por bloco:", "", "```json", "{",
          '  "envio": { "contrato": "' + c.contrato + '", "versao_layout": "' + c.versao + '", "...": "..." },']
    for i, b in enumerate(c.blocos):
        virgula = "," if i < len(c.blocos) - 1 else ""
        l.append(f'  "{b.nome}": [ {{ }} ]{virgula}')
    l += ["}", "```", "", "No Excel, o cabeçalho fica na aba `envio` (campo/valor) e cada bloco numa aba própria.", ""]

    l += ["## Cabeçalho (`envio`)", ""]
    l += _tabela_campos(c.cabecalho)
    l.append(f"| `totais` | objeto | Sim | um inteiro ≥ 0 por bloco: {', '.join(c.nomes_blocos)} | "
             "Quantidade de registros de cada bloco (R08). | gerado pela ferramenta |")
    l.append("")

    for b in c.blocos:
        l += [f"## Bloco `{b.nome}`", ""]
        if b.descricao:
            l += [b.descricao.strip(), ""]
        if b.chave:
            l += [f"**Chave única:** {', '.join(f'`{k}`' for k in b.chave)}", ""]
        l += _tabela_campos(b.campos)
        l.append("")

    l += ["## Regras de recebimento", "", "### Automáticas", "",
          "| Id | Regra | Efeito |", "|---|---|---|"]
    for rid, desc in REGRAS_AUTOMATICAS.items():
        l.append(f"| {rid} | {_cel(desc)} | rejeição |")
    l.append("")
    if c.regras:
        l += ["### Do contrato", "", "| Id | Tipo | Bloco | Condição | Mensagem | Efeito |",
              "|---|---|---|---|---|---|"]
        for r in c.regras:
            efeito = "rejeição" if r.severidade == "rejeicao" else "alerta"
            l.append(f"| {r.id} | {r.tipo} | `{r.bloco}` | {_cel(_descricao_regra(r))} | {_cel(r.mensagem)} | {efeito} |")
        l.append("")
    l += ["Regras de **rejeição** recusam o envio; **alertas** são registrados, mas o envio é aceito.", ""]
    return "\n".join(l)
