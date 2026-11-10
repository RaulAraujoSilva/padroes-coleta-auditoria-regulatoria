# -*- coding: utf-8 -*-
"""
Converte um envio no layout IPG 1.0 (JSON — vindo da API, do Excel convertido ou
do arquivo JSON) nos CSVs que o verificador da AGENERSA consome
(verificador/autovistoria.py): unidades.csv, inspecoes.csv e habilitacoes.csv.

Uso:
  python json_para_verificador.py ENVIO.json PASTA_SAIDA
  python ../verificador/autovistoria.py --pasta PASTA_SAIDA --data-base AAAA-MM-DD \
         --oia ../verificador/dados/oia_inmetro.csv
"""
import csv
import json
import sys
from pathlib import Path

CONC = {"CEG": "CEG", "CEG_RIO": "CEG RIO"}


def gravar(caminho: Path, campos: list[str], linhas: list[dict]) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)


def converter(envio: dict, saida: Path) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    cab = envio["envio"]
    conc = CONC[cab["remetente"]]

    unidades = [{
        "id_unidade": u["id_unidade"], "concessionaria": conc,
        "municipio": u["municipio"], "bairro": u.get("bairro") or "",
        "classe": u["classe"], "situacao_fornecimento": u["situacao_fornecimento"],
        "data_vistoria_previa": u.get("data_vistoria_previa") or "",
    } for u in envio["unidades"]]

    # 1ª interrupção registrada para cada laudo
    corte: dict[str, str] = {}
    for it in envio.get("interrupcoes", []):
        o = it.get("id_inspecao_origem")
        if o and (o not in corte or it["data_interrupcao"] < corte[o]):
            corte[o] = it["data_interrupcao"]

    inspecoes = [{
        "id_inspecao": i["id_inspecao"], "id_unidade": i["id_unidade"],
        "data_inspecao": i["data_inspecao"], "doc_inspetora": i["documento_inspetora"],
        "resultado": i["resultado"],
        "registro_profissional": f"{i.get('responsavel_tecnico_conselho') or ''} {i.get('responsavel_tecnico_registro') or ''}".strip(),
        "prazo_adequacao": i.get("prazo_adequacao") or "",
        "escapamento": "SIM" if i.get("escapamento_gas") else "",
        "data_interrupcao": corte.get(i["id_inspecao"], ""),
    } for i in envio["inspecoes"]]

    habilitacoes = [{
        "doc_inspetora": h["documento_inspetora"],
        "tipo": "CREDENCIADA_" + cab["remetente"],
        "numero": "", "inicio": h["data_inicio"], "fim": h.get("data_fim") or "",
    } for h in envio.get("inspetoras_credenciadas", [])]

    gravar(saida / "unidades.csv", list(unidades[0]) if unidades else ["id_unidade"], unidades)
    gravar(saida / "inspecoes.csv", ["id_inspecao", "id_unidade", "data_inspecao", "doc_inspetora", "resultado",
                                     "registro_profissional", "prazo_adequacao", "escapamento", "data_interrupcao"], inspecoes)
    gravar(saida / "habilitacoes.csv", ["doc_inspetora", "tipo", "numero", "inicio", "fim"], habilitacoes)
    return {"unidades": len(unidades), "inspecoes": len(inspecoes), "habilitacoes": len(habilitacoes),
            "data_referencia": cab["data_referencia"]}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    r = converter(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), Path(sys.argv[2]))
    print(f"Convertido: {r['unidades']} unidades, {r['inspecoes']} inspeções, "
          f"{r['habilitacoes']} credenciamentos (data de referência {r['data_referencia']}) -> {sys.argv[2]}")
