# -*- coding: utf-8 -*-
"""
Verificador computável da AUTOVISTORIA QUINQUENAL de gás canalizado (RJ).

Base normativa (texto lido nas fontes, não na citação de origem):
  - Lei Estadual RJ nº 6.890/2014 (vigência: 21/03/2015)
  - IN AGENERSA nº 113/2024 (DOERJ 16/01/2024), que revogou a IN 47/2015 e a IN 73/2018,
    com cronograma alterado pelas IN 136/2025 e IN 149/2026
  - IN AGENERSA nº 48/2015 (Regulamento e Manual da rede de distribuição interna;
    arts. 2º e 3º: OIA acreditado pelo Inmetro) — não revogada expressamente pela IN 113
  - ABNT NBR 15923 (prazo para irregularidade sanável) e NBR 13103 (teste de CO)

Entradas (CSV, UTF-8):
  unidades.csv     id_unidade, concessionaria, municipio, bairro, classe,
                   situacao_fornecimento, [data_vistoria_previa]
  inspecoes.csv    id_inspecao, id_unidade, data_inspecao, doc_inspetora,
                   resultado, [registro_profissional], [prazo_adequacao], [escapamento],
                   [data_interrupcao]
  habilitacoes.csv doc_inspetora, tipo, [numero], inicio, [fim]
                   tipo ∈ {OIA_INMETRO, CREDENCIADA_CEG, CREDENCIADA_CEG_RIO}
  dados/cronograma_ipg.csv  (gerado por extrair_cronograma.py)

Uso:
  python exemplos/ipg-gas-rj/verificador/autovistoria.py --data-base 2026-11-10
  (sem --pasta, usa a pasta exemplo/ ao lado do script; --oia acrescenta a lista OIA-IG da Cgcre)
"""
from __future__ import annotations

import argparse
import csv
import json
import unicodedata
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).parent

# ---------------------------------------------------------------- utilidades


def d(s: str | None) -> date | None:
    s = (s or "").strip()
    if not s:
        return None
    if "/" in s:
        dd, mm, aa = s.split("/")
        return date(int(aa), int(mm), int(dd))
    return date.fromisoformat(s)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def somar_anos(dt: date, anos: int, modo: str) -> date:
    if modo == "365_25":
        return dt + timedelta(days=round(anos * 365.25))
    try:
        return dt.replace(year=dt.year + anos)
    except ValueError:  # 29/02 em ano não bissexto
        return dt.replace(year=dt.year + anos, day=28)


def somar_dias_uteis(dt: date, n: int) -> date:
    while n > 0:
        dt += timedelta(days=1)
        if dt.weekday() < 5:
            n -= 1
    return dt


def ler_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


# ---------------------------------------------------------------- resultado


@dataclass
class Veredito:
    id_unidade: str
    status: str
    data_limite: date | None = None
    dias_atraso: int | None = None
    ultima_inspecao_valida: str = ""
    obrigacao_concessionaria: str = "OK"
    justificativa: list[str] = field(default_factory=list)
    lacunas_acionadas: set[str] = field(default_factory=set)
    inspecoes_desconsideradas: list[str] = field(default_factory=list)

    def linha(self) -> dict:
        return {
            "id_unidade": self.id_unidade,
            "status": self.status,
            "data_limite": self.data_limite.isoformat() if self.data_limite else "",
            "dias_atraso": "" if self.dias_atraso is None else self.dias_atraso,
            "ultima_inspecao_valida": self.ultima_inspecao_valida,
            "obrigacao_concessionaria": self.obrigacao_concessionaria,
            "inspecoes_desconsideradas": " | ".join(self.inspecoes_desconsideradas),
            "lacunas_acionadas": ",".join(sorted(self.lacunas_acionadas)),
            "justificativa": " | ".join(self.justificativa),
        }


# ---------------------------------------------------------------- motor


class Verificador:
    def __init__(self, params: dict, habilitacoes: list[dict], cronograma: list[dict]):
        self.p = params
        self.hab: dict[str, list[dict]] = {}
        for h in habilitacoes:
            self.hab.setdefault(re.sub(r"\D", "", h["doc_inspetora"]), []).append(h)
        col = "fim_pela_regra" if params["cronograma_prevalece"] == "regra" else "fim_vigente"
        self.crono: dict[tuple[str, str], dict] = {}
        for c in cronograma:
            chave = (norm(c["municipio"]), norm(c["bairro"]) if c["bairro"] != "*" else "*")
            self.crono[chave] = {**c, "_fim": d(c[col]), "_div": c.get("divergente") == "SIM"}

    # R1 — a inspetora estava habilitada NA DATA da inspeção?
    def habilitada(self, doc: str, data_insp: date, concessionaria: str) -> tuple[bool, str, set]:
        lac: set[str] = set()
        regs = self.hab.get(re.sub(r"\D", "", doc), [])
        if not regs:
            return False, "inspetora sem nenhuma habilitação cadastrada", lac
        vigentes = [h for h in regs if d(h["inicio"]) <= data_insp and (not d(h.get("fim")) or data_insp <= d(h["fim"]))]
        if data_insp < d(self.p["inicio_regime_in113"]):
            lac.add("L2")
            aceitos = set(self.p["habilitacao_aceita_antes_in113"])
            ok = [h for h in vigentes if h["tipo"] in aceitos]
            return (bool(ok), f"regime IN 47/2015: {'habilitada (' + ok[0]['tipo'] + ')' if ok else 'sem acreditação/credenciamento aceito vigente na data'}", lac)
        aceitos = set(self.p["habilitacao_aceita_desde_in113"])
        corte = d(self.p["inicio_regime_in113"])
        for h in vigentes:
            t = h["tipo"]
            if t == "OIA_INMETRO" and t in aceitos:
                lac.add("L10")  # a consulta da Cgcre não mostra suspensões já encerradas
                if d(h["inicio"]) < corte:
                    return True, f"OIA Inmetro {h.get('numero', '')} acreditado antes da IN 113 (dispensa do art. 2º, IV)", lac
                lac.add("L1")
                if self.p["oia_inmetro_apos_in113"] == "todos":
                    return True, f"OIA Inmetro {h.get('numero', '')} acreditado após a IN 113 (IN 48/2015, arts. 2º e 3º)", lac
            if t.startswith("CREDENCIADA_") and t in aceitos:
                propria = t == "CREDENCIADA_" + norm(concessionaria).replace(" ", "_")
                if propria:
                    return True, f"credenciada pela {concessionaria}", lac
                lac.add("L3")
                if self.p["credenciamento_vale_para_outra_concessionaria"]:
                    return True, f"credenciada por outra concessionária ({t})", lac
        return False, "regime IN 113/2024: sem credenciamento da concessionária nem OIA aceito vigente na data", lac

    def prazo_primeira(self, u: dict, v: Veredito) -> date | None:
        mun, bai = norm(u["municipio"]), norm(u.get("bairro", ""))
        c = self.crono.get((mun, bai)) or self.crono.get((mun, "*"))
        if c:
            if c["_div"]:
                v.lacunas_acionadas.add("L6")
            v.justificativa.append(f"1ª inspeção: cronograma {c['fundamento_fim']} ({c['bairro'] if c['bairro'] != '*' else c['municipio']})")
            return c["_fim"]
        v.lacunas_acionadas.add("L6")
        v.justificativa.append("localidade fora do Anexo I: prazo geral do art. 8º da IN 113")
        return d(self.p["prazo_primeira_sem_cronograma"])

    def avaliar(self, u: dict, inspecoes: list[dict], data_base: date) -> Veredito:
        p = self.p
        v = Veredito(u["id_unidade"], "INDETERMINADO")

        # R0 — escopo
        if norm(u.get("classe", "")) not in p["classes_no_escopo"]:
            v.status = "FORA_DO_ESCOPO"
            v.justificativa.append(f"classe '{u.get('classe')}' não é residencial/comercial")
            return v
        if norm(u.get("situacao_fornecimento", "ATIVO")) != "ATIVO":
            v.lacunas_acionadas.add("L9")
            if not p["incluir_unidades_sem_fornecimento"]:
                v.status = "FORA_DO_ESCOPO"
                v.justificativa.append("sem fornecimento ativo")
                return v

        # R1 — filtra inspeções válidas
        validas = []
        for i in sorted(inspecoes, key=lambda x: d(x["data_inspecao"]) or date.min):
            di = d(i["data_inspecao"])
            if di is None or di > data_base:
                continue
            if di < d(p["inicio_vigencia_lei"]):
                v.inspecoes_desconsideradas.append(f"{i['id_inspecao']}: anterior à vigência da lei")
                continue
            ok, motivo, lac = self.habilitada(i["doc_inspetora"], di, u["concessionaria"])
            v.lacunas_acionadas |= lac
            if ok and p["exigir_registro_profissional"] and di >= d(p["inicio_regime_in113"]) and not i.get("registro_profissional"):
                ok, motivo = False, "sem registro CREA/CAU/CRT informado"
            if not ok:
                v.inspecoes_desconsideradas.append(f"{i['id_inspecao']}: {motivo}")
                continue
            if norm(i["resultado"]) not in p["resultados_que_contam_como_inspecao"]:
                v.lacunas_acionadas.add("L7")
                v.inspecoes_desconsideradas.append(f"{i['id_inspecao']}: resultado '{i['resultado']}' não conta")
                continue
            validas.append(i)

        # R2 — tempestividade
        if validas:
            ult = validas[-1]
            du = d(ult["data_inspecao"])
            v.ultima_inspecao_valida = f"{ult['id_inspecao']} ({du:%d/%m/%Y}, {ult['resultado']})"
            v.data_limite = somar_anos(du, p["periodicidade_anos"], p["contagem_prazo"])
            v.lacunas_acionadas.add("L4")
            v.justificativa.append("prazo contado da inspeção mais recente (IN 113, art. 8º)")
        elif u.get("data_vistoria_previa") and p["vistoria_previa_inicia_contagem"]:
            v.lacunas_acionadas.add("L5")
            v.data_limite = somar_anos(d(u["data_vistoria_previa"]), p["periodicidade_anos"], p["contagem_prazo"])
            v.justificativa.append("prazo contado da vistoria prévia da concessionária (IN 113, art. 4º)")
        else:
            v.data_limite = self.prazo_primeira(u, v)

        if v.data_limite is None:
            v.justificativa.append("não foi possível determinar a data-limite")
            return v

        atraso = (data_base - v.data_limite).days
        if atraso > 0:
            v.dias_atraso = atraso
            v.status = "VENCIDA" if validas or u.get("data_vistoria_previa") else "PRIMEIRA_NAO_REALIZADA"
        else:
            v.status = "EM_DIA" if validas else "PRIMEIRA_PENDENTE_NO_PRAZO"

        # R3 / R4 — consequências do resultado da última inspeção válida
        if validas and v.status == "EM_DIA":
            ult = validas[-1]
            res = norm(ult["resultado"])
            prazo = d(ult.get("prazo_adequacao"))
            if res == "APROVADO_COM_RESTRICAO" and prazo and data_base > prazo:
                v.status = "ADEQUACAO_VENCIDA"
                v.justificativa.append(f"prazo de adequação (NBR 15923) venceu em {prazo:%d/%m/%Y} sem nova inspeção")
            if res == "REPROVADO":
                v.status = "REPROVADA"
            if res == "REPROVADO" or v.status == "ADEQUACAO_VENCIDA":
                v.lacunas_acionadas.add("L8")
                di = d(ult["data_inspecao"]) if res == "REPROVADO" else prazo
                dc = d(ult.get("data_interrupcao"))
                v.lacunas_acionadas.add("L11")
                imediato = norm(ult.get("escapamento", "")) in ("SIM", "S", "TRUE", "1")
                limite = di if imediato else somar_dias_uteis(di, p["prazo_interrupcao_dias_uteis"])
                if dc is None or dc > limite:
                    v.obrigacao_concessionaria = ("NAO_INTERROMPEU" if p["interrupcao_obrigatoria_apos_reprovacao"]
                                                  else "VERIFICAR_AVALIACAO_DE_INTERRUPCAO")
                    v.justificativa.append("sem interrupção do fornecimento no prazo (Lei 6.890, art. 4º)")
        return v


# ---------------------------------------------------------------- CLI


def rodar(pasta: Path, data_base: date, params_path: Path, crono_path: Path,
          oia_path: Path | None = None) -> list[Veredito]:
    params = json.loads(params_path.read_text(encoding="utf-8"))
    hab = ler_csv(pasta / "habilitacoes.csv")
    if oia_path and oia_path.exists():          # lista oficial da Cgcre (baixar_oia_inmetro.py)
        hab += ler_csv(oia_path)
    ver = Verificador(params, hab, ler_csv(crono_path))
    insp: dict[str, list[dict]] = {}
    for i in ler_csv(pasta / "inspecoes.csv"):
        insp.setdefault(i["id_unidade"], []).append(i)
    return [ver.avaliar(u, insp.get(u["id_unidade"], []), data_base) for u in ler_csv(pasta / "unidades.csv")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-base", default=date.today().isoformat())
    ap.add_argument("--pasta", default=str(AQUI / "exemplo"))
    ap.add_argument("--parametros", default=str(AQUI / "parametros.json"))
    ap.add_argument("--cronograma", default=str(AQUI / "dados" / "cronograma_ipg.csv"))
    ap.add_argument("--oia", default="", help="CSV de OIA-IG da Cgcre (ex.: dados/oia_inmetro.csv)")
    ap.add_argument("--saida", default="")
    a = ap.parse_args()
    res = rodar(Path(a.pasta), d(a.data_base), Path(a.parametros), Path(a.cronograma),
                Path(a.oia) if a.oia else None)
    linhas = [r.linha() for r in res]
    if a.saida:
        with open(a.saida, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
            w.writeheader()
            w.writerows(linhas)
    from collections import Counter
    print(f"Data-base {d(a.data_base):%d/%m/%Y} — {len(res)} unidades")
    for st, n in Counter(r.status for r in res).most_common():
        print(f"  {st:28s} {n}")
    print(f"  concessionária sem interrupção: {sum(r.obrigacao_concessionaria != 'OK' for r in res)}")
    print()
    for l in linhas:
        print(f"{l['id_unidade']:6s} {l['status']:27s} limite={l['data_limite'] or '-':10s} "
              f"conc={l['obrigacao_concessionaria']:16s} lacunas=[{l['lacunas_acionadas']}]")
        if l["inspecoes_desconsideradas"]:
            print(f"       desconsideradas: {l['inspecoes_desconsideradas']}")


if __name__ == "__main__":
    main()
