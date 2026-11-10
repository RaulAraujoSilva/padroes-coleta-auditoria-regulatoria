# -*- coding: utf-8 -*-
# Exercício: regra computável a partir SOMENTE do texto:
# "As instalações internas de gás canalizado devem passar por autovistoria de segurança
#  a cada 5 anos, executada por empresa credenciada pelo Inmetro."
#  (Lei Estadual RJ nº 6.890/2014 · IN AGENERSA CODIR nº 48/2015 · ABNT NBR 15923)

from datetime import date, timedelta  # importa os tipos de data e de intervalo de dias

CONFORME = "CONFORME"  # saída quando a regra é cumprida
NAO_CONFORME = "NÃO CONFORME"  # saída quando a regra é descumprida
DELIBERAR = "PRECISA DE DELIBERAÇÃO"  # saída quando o texto é ambíguo ou o dado é incoerente


def _mais_5_anos_civis(d: date) -> date:  # soma 5 anos pelo calendário (mesmo dia e mês)
    try:  # tenta manter o mesmo dia e mês
        return d.replace(year=d.year + 5)  # devolve a data 5 anos depois
    except ValueError:  # 29/02 não existe no ano de destino
        return d.replace(year=d.year + 5, day=28)  # usa 28/02 nesse caso


def _credenciada_em(periodos: list, dia: date) -> bool:  # diz se algum período de credenciamento cobre o dia
    return any(ini <= dia and (fim is None or dia <= fim) for ini, fim in periodos)  # fim vazio = ainda credenciada


def verificar_autovistoria(data_referencia: date,  # dia em que o fiscal faz a verificação
                           eh_gas_canalizado,  # True, False ou None (desconhecido)
                           data_ultima_autovistoria,  # data da última autovistoria ou None
                           cnpj_executora,  # CNPJ da empresa que executou ou None
                           credenciamentos_inmetro: dict):  # CNPJ -> lista de (início, fim) de credenciamento no Inmetro
    if eh_gas_canalizado is None:  # não se sabe se a instalação é de gás canalizado
        return DELIBERAR, "Não se sabe se a instalação é de gás canalizado; sem isso não dá para saber se o texto se aplica."  # não chuta
    if eh_gas_canalizado is False:  # a instalação não é de gás canalizado
        return DELIBERAR, "O texto só trata de gás canalizado; ele não diz o que vale para outras instalações."  # fora do alcance do texto
    if data_ultima_autovistoria is None:  # nunca houve autovistoria registrada
        return DELIBERAR, "Não há autovistoria registrada e o texto não diz a partir de quando conta o primeiro prazo de 5 anos."  # trecho ambíguo
    if data_ultima_autovistoria > data_referencia:  # autovistoria com data no futuro
        return DELIBERAR, f"Dado incoerente: autovistoria em {data_ultima_autovistoria:%d/%m/%Y}, depois da data da verificação."  # erro de dado
    if not cnpj_executora:  # não se sabe quem executou
        return DELIBERAR, "Falta o CNPJ da empresa executora; sem ele não dá para conferir o credenciamento no Inmetro."  # dado incompleto

    limite_curto = min(_mais_5_anos_civis(data_ultima_autovistoria),  # leitura 1: 5 anos de calendário
                       data_ultima_autovistoria + timedelta(days=5 * 365))  # leitura 2: 1.825 dias
    limite_longo = max(_mais_5_anos_civis(data_ultima_autovistoria),  # leitura 1 de novo
                       data_ultima_autovistoria + timedelta(days=1826))  # leitura 3: 1.826 dias (com o ano bissexto)
    if data_referencia > limite_longo:  # vencida em qualquer leitura de "5 anos"
        return NAO_CONFORME, (f"Última autovistoria em {data_ultima_autovistoria:%d/%m/%Y}; "  # informa a data da vistoria
                              f"o prazo de 5 anos terminou até {limite_longo:%d/%m/%Y}.")  # e quando o prazo acabou
    if data_referencia > limite_curto:  # vencida numa leitura e não na outra
        return DELIBERAR, ("A data cai na faixa em que o resultado depende de como se contam os 5 anos "  # explica a ambiguidade
                           f"({limite_curto:%d/%m/%Y} a {limite_longo:%d/%m/%Y}); o texto não define a contagem.")  # mostra a faixa

    periodos = credenciamentos_inmetro.get(cnpj_executora, [])  # busca os períodos de credenciamento da empresa
    na_data_vistoria = _credenciada_em(periodos, data_ultima_autovistoria)  # credenciada quando fez a vistoria?
    na_data_referencia = _credenciada_em(periodos, data_referencia)  # credenciada hoje?
    if not na_data_vistoria and not na_data_referencia:  # não era credenciada em nenhum dos dois momentos
        return NAO_CONFORME, f"A empresa {cnpj_executora} não consta como credenciada pelo Inmetro."  # descumpre a exigência
    if na_data_vistoria != na_data_referencia:  # credenciada em só um dos momentos
        return DELIBERAR, ("A empresa era credenciada pelo Inmetro em apenas um dos momentos (data da vistoria ou hoje); "  # descreve o caso
                           "o texto não diz em qual data o credenciamento deve valer.")  # trecho ambíguo
    return CONFORME, (f"Autovistoria em {data_ultima_autovistoria:%d/%m/%Y}, dentro de 5 anos, "  # cumpre o prazo
                      f"por empresa credenciada pelo Inmetro ({cnpj_executora}).")  # e foi feita por empresa credenciada


if __name__ == "__main__":  # bloco de teste, roda só quando o arquivo é executado direto
    hoje = date(2026, 11, 10)  # data fictícia da verificação
    inmetro = {"22.334.455/0001-86": [(date(2016, 1, 1), None)],  # empresa A: credenciada desde 2016
               "44.555.666/0001-81": [(date(2018, 1, 1), date(2022, 12, 31))]}  # empresa B: credenciamento encerrado em 2022
    casos = [  # (nome, entradas, saída esperada)
        ("Caso 1 — vistoria de 2023 pela empresa A", (hoje, True, date(2023, 5, 10), "22.334.455/0001-86", inmetro), CONFORME),  # deve passar
        ("Caso 2 — vistoria de 2019 pela empresa A", (hoje, True, date(2019, 6, 1), "22.334.455/0001-86", inmetro), NAO_CONFORME),  # prazo vencido
        ("Caso 3 — vistoria de 2022 pela empresa B", (hoje, True, date(2022, 3, 1), "44.555.666/0001-81", inmetro), DELIBERAR),  # credenciada só na época
    ]
    for nome, entradas, esperado in casos:  # percorre os casos
        obtido, motivo = verificar_autovistoria(*entradas)  # aplica a regra
        marca = "OK" if obtido == esperado else "DIVERGENTE"  # compara obtido com esperado
        print(f"{nome}\n  esperado: {esperado}\n  obtido:   {obtido}  [{marca}]\n  justificativa: {motivo}\n")  # mostra o resultado
