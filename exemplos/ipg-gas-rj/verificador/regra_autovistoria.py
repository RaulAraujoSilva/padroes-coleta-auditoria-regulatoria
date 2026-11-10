# -*- coding: utf-8 -*-
"""
Regra computável — autovistoria quinquenal de gás canalizado (RJ).
Lei 6.890/2014 · IN AGENERSA 48/2015 e 113/2024 (alt. IN 136/2025 e 149/2026) · NBR 15923

Versão didática: cada função corresponde a um item da regra (1 a 6) e cada
decisão que a norma não toma é um parâmetro (P1 a P8).
"""
from dataclasses import dataclass
from datetime import date, timedelta

# ------------------------------------------------------------------ constantes legais
VIGENCIA_LEI = date(2015, 3, 21)        # Lei 6.890, art. 5º (180 dias após 22/09/2014)
INICIO_IN113 = date(2024, 1, 16)        # IN 113/2024 publicada no DOERJ
PRAZO_GERAL_1A = date(2026, 3, 22)      # IN 113, art. 8º (localidade fora do cronograma)
PERIODICIDADE = 5                       # anos
DIAS_UTEIS_CORTE = 15                   # IN 48/2015, item 4.1.20


# ------------------------------------------------------------------ parâmetros (lacunas)
@dataclass
class Parametros:
    p1_oia_pos_in113_vale: bool = True          # OIA acreditado após jan/2024 vale sem credenciamento?
    p2_credenciamento_cruzado: bool = False     # credenciada CEG vale para CEG RIO?
    p3_reprovada_conta: bool = True             # inspeção reprovada cumpre a periodicidade?
    p4_contagem: str = "aniversario"            # "aniversario" ou "365_25"
    p5_vistoria_previa_inicia: bool = True      # vistoria prévia da concessionária inicia a contagem?
    p6_cronograma: str = "tabela"               # "tabela" (Anexo publicado) ou "regra" (art. 1º)
    p7_desligada_obrigada: bool = False         # unidade sem fornecimento continua obrigada?
    p8_interrupcao_obrigatoria: bool = True     # lei (obrigatória) x IN 113 art. 7º (avaliar)


# ------------------------------------------------------------------ dados de entrada
@dataclass
class Unidade:
    id: str
    concessionaria: str                 # "CEG" | "CEG RIO"
    municipio: str
    bairro: str
    classe: str                         # "RESIDENCIAL" | "COMERCIAL" | ...
    fornecimento_ativo: bool
    data_vistoria_previa: date | None = None


@dataclass
class Inspecao:
    id: str
    data: date
    doc_inspetora: str                  # CNPJ/CPF
    resultado: str                      # "APROVADO" | "APROVADO_COM_RESTRICAO" | "REPROVADO"
    registro_profissional: str = ""     # CREA/CAU/CRT
    prazo_adequacao: date | None = None
    escapamento: bool = False
    data_interrupcao: date | None = None


@dataclass
class Habilitacao:
    doc_inspetora: str
    tipo: str                           # "OIA_INMETRO" | "CREDENCIADA_CEG" | "CREDENCIADA_CEG_RIO"
    inicio: date                        # concessão da acreditação / início do credenciamento
    fim: date | None = None             # suspensão, cancelamento ou fim do credenciamento

    def vigente(self, t: date) -> bool:
        return self.inicio <= t and (self.fim is None or t <= self.fim)


# ------------------------------------------------------------------ utilidades de data
def mais_anos(dt: date, anos: int, modo: str) -> date:
    if modo == "365_25":
        return dt + timedelta(days=round(anos * 365.25))
    try:
        return dt.replace(year=dt.year + anos)
    except ValueError:                  # 29/02 -> 28/02
        return dt.replace(year=dt.year + anos, day=28)


def mais_dias_uteis(dt: date, n: int) -> date:
    while n:
        dt += timedelta(days=1)
        n -= dt.weekday() < 5
    return dt


# ------------------------------------------------------------------ regra
class RegraAutovistoria:
    def __init__(self, p: Parametros, habilitacoes: list[Habilitacao],
                 cronograma: dict[tuple[str, str], dict]):
        """cronograma[(MUNICIPIO, BAIRRO ou '*')] = {"tabela": date, "regra": date}"""
        self.p, self.cron = p, cronograma
        self.hab: dict[str, list[Habilitacao]] = {}
        for h in habilitacoes:
            self.hab.setdefault(h.doc_inspetora, []).append(h)

    # 1. Escopo
    def no_escopo(self, u: Unidade) -> bool:
        return (u.concessionaria in ("CEG", "CEG RIO")
                and u.classe in ("RESIDENCIAL", "COMERCIAL")
                and (u.fornecimento_ativo or self.p.p7_desligada_obrigada))

    # 2. Habilitada(i, t, u)
    def habilitada(self, doc: str, t: date, u: Unidade) -> bool:
        vigentes = [h for h in self.hab.get(doc, []) if h.vigente(t)]
        if t < INICIO_IN113:
            return any(h.tipo == "OIA_INMETRO" for h in vigentes)
        propria = "CREDENCIADA_" + u.concessionaria.replace(" ", "_")
        for h in vigentes:
            if h.tipo == "OIA_INMETRO" and (h.inicio < INICIO_IN113 or self.p.p1_oia_pos_in113_vale):
                return True                                          # (a) e (b)
            if h.tipo == propria or (h.tipo.startswith("CREDENCIADA_") and self.p.p2_credenciamento_cruzado):
                return True                                          # (c)
        return False

    # 3. Inspeção válida
    def valida(self, i: Inspecao, u: Unidade, D: date) -> bool:
        if not (VIGENCIA_LEI <= i.data <= D):
            return False
        if not self.habilitada(i.doc_inspetora, i.data, u):
            return False
        if i.data >= INICIO_IN113 and not i.registro_profissional:   # IN 113, art. 2º, IV
            return False
        return i.resultado != "REPROVADO" or self.p.p3_reprovada_conta

    # 4. Data-limite L(u)
    def data_limite(self, u: Unidade, ult: Inspecao | None) -> date:
        if ult:
            return mais_anos(ult.data, PERIODICIDADE, self.p.p4_contagem)
        if u.data_vistoria_previa and self.p.p5_vistoria_previa_inicia:
            return mais_anos(u.data_vistoria_previa, PERIODICIDADE, self.p.p4_contagem)
        c = self.cron.get((u.municipio, u.bairro)) or self.cron.get((u.municipio, "*"))
        return c[self.p.p6_cronograma] if c else PRAZO_GERAL_1A

    # 5 e 6. Veredito do usuário e da concessionária
    def avaliar(self, u: Unidade, inspecoes: list[Inspecao], D: date) -> dict:
        if not self.no_escopo(u):
            return {"unidade": u.id, "status": "FORA_DO_ESCOPO"}

        validas = sorted((i for i in inspecoes if self.valida(i, u, D)), key=lambda i: i.data)
        ult = validas[-1] if validas else None
        L = self.data_limite(u, ult)

        # 5. obrigação do usuário
        if D > L:
            status = "VENCIDA" if (ult or u.data_vistoria_previa) else "PRIMEIRA_NAO_REALIZADA"
        elif ult is None:
            status = "PRIMEIRA_PENDENTE_NO_PRAZO"
        elif ult.resultado == "REPROVADO":
            status = "REPROVADA"
        elif ult.resultado == "APROVADO_COM_RESTRICAO" and ult.prazo_adequacao and D > ult.prazo_adequacao:
            status = "ADEQUACAO_VENCIDA"
        else:
            status = "CONFORME"

        # 6. obrigação da concessionária (independe do status do usuário)
        conc = "OK"
        if ult:
            gatilho = None
            if ult.resultado == "REPROVADO":
                gatilho = ult.data
            elif ult.resultado == "APROVADO_COM_RESTRICAO" and ult.prazo_adequacao and D > ult.prazo_adequacao:
                gatilho = ult.prazo_adequacao
            if gatilho:
                limite = gatilho if ult.escapamento else mais_dias_uteis(gatilho, DIAS_UTEIS_CORTE)
                if D > limite and (ult.data_interrupcao is None or ult.data_interrupcao > limite):
                    conc = "NAO_INTERROMPEU" if self.p.p8_interrupcao_obrigatoria \
                        else "VERIFICAR_AVALIACAO_DE_INTERRUPCAO"

        return {"unidade": u.id, "status": status, "data_limite": L,
                "dias_atraso": max((D - L).days, 0), "ultima_inspecao": ult.id if ult else None,
                "concessionaria": conc,
                "desconsideradas": [i.id for i in inspecoes if i not in validas and i.data <= D]}


# ------------------------------------------------------------------ exemplo
if __name__ == "__main__":
    D = date(2026, 11, 10)
    hab = [
        Habilitacao("90.123.456/0001-31", "OIA_INMETRO", date(2016, 10, 5)),        # fictícia, acreditada antes da IN 113
        Habilitacao("44.555.666/0001-81", "CREDENCIADA_CEG", date(2024, 2, 1)),     # fictícia
        Habilitacao("99.887.766/0001-05", "OIA_INMETRO", date(2024, 3, 10)),        # fictícia, pós-IN 113
    ]
    cron = {("RIO DE JANEIRO", "MADUREIRA"): {"tabela": date(2026, 3, 22), "regra": date(2026, 9, 23)}}
    regra = RegraAutovistoria(Parametros(), hab, cron)

    casos = [
        (Unidade("U1", "CEG", "RIO DE JANEIRO", "COPACABANA", "RESIDENCIAL", True),
         [Inspecao("I1", date(2023, 5, 10), "90.123.456/0001-31", "APROVADO")]),
        (Unidade("U2", "CEG", "RIO DE JANEIRO", "MADUREIRA", "RESIDENCIAL", True), []),
        (Unidade("U3", "CEG", "RIO DE JANEIRO", "TIJUCA", "COMERCIAL", True),
         [Inspecao("I3", date(2019, 6, 1), "90.123.456/0001-31", "APROVADO")]),
        (Unidade("U4", "CEG", "NITEROI", "*", "RESIDENCIAL", True),
         [Inspecao("I4", date(2026, 1, 15), "44.555.666/0001-81", "REPROVADO", "CREA-RJ 123")]),
        (Unidade("U5", "CEG RIO", "MACAE", "*", "RESIDENCIAL", True),
         [Inspecao("I5", date(2025, 6, 10), "44.555.666/0001-81", "APROVADO", "CREA-RJ 123")]),
        (Unidade("U6", "CEG", "RIO DE JANEIRO", "IPANEMA", "RESIDENCIAL", True),
         [Inspecao("I6", date(2024, 5, 1), "99.887.766/0001-05", "APROVADO", "CREA-RJ 777")]),
    ]
    for u, insp in casos:
        print(regra.avaliar(u, insp, D))
