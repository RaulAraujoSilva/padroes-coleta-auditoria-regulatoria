# Caso-exemplo: inspeção quinquenal de gás canalizado no Rio de Janeiro

Este caso aplica o método do repositório, do começo ao fim, a uma obrigação real: a **autovistoria quinquenal de segurança das instalações internas de gás canalizado** no Estado do Rio de Janeiro, fiscalizada pela AGENERSA sobre as concessionárias **CEG** e **CEG RIO**.

| Arquivo | Conteúdo |
|---|---|
| [`contrato.yaml`](contrato.yaml) | contrato de coleta `ipg-envio` 1.0: teste de auditoria, lacunas, blocos, campos e regras de recebimento |
| [`envios/`](envios/) | um envio completo e um incremental, com dados fictícios |
| [`verificador/`](verificador/) | a regra em Python: versão "só o texto", versão didática, motor completo, parâmetros, testes e scripts que buscam os dados públicos |

## 1. A norma e a regra citada

A regra chegou à fiscalização assim:

> "As instalações internas de gás canalizado devem passar por autovistoria de segurança a cada 5 anos, executada por empresa credenciada pelo Inmetro." (Lei Estadual RJ nº 6.890/2014 · IN AGENERSA CODIR nº 48/2015 · ABNT NBR 15923)

Normas envolvidas:

- Lei Estadual nº 6.890/2014, em vigor desde 21/03/2015;
- IN AGENERSA nº 48/2015 e nº 113/2024, esta alterada pelas INs nº 136/2025 e nº 149/2026;
- ABNT NBR 15923 e NBR 13103.

## 2. O que a leitura das fontes revelou

A primeira etapa do método é **ler a norma vigente, não a citação**. A leitura dos textos integrais mudou a regra em quatro pontos.

| Achado | O que as fontes dizem |
|---|---|
| **A regra citada está desatualizada** | A Lei 6.890 fala em "empresas inspetoras credenciadas", sem dizer por quem. Quem nomeia o Inmetro é a IN 48/2015 (arts. 2º e 3º). Desde a IN 113/2024 (DOERJ 16/01/2024), o credenciamento é feito pela **CEG e pela CEG RIO** (art. 2º, I). Podem ser credenciadas pessoas físicas ou jurídicas com registro em dia no CREA-RJ, no CAU-RJ ou no CRT. Quem "estava acreditado perante o INMETRO" fica dispensado de novo credenciamento (art. 2º, IV). |
| **A IN 48 não foi revogada** | A IN 113 revogou expressamente as INs 47/2015 e 73/2018, mas não a IN 48/2015. As duas convivem: uma aceita o OIA acreditado pelo Inmetro; a outra, pela leitura literal, só aceita quem já estava acreditado em janeiro de 2024. |
| **O cronograma se contradiz em 49 localidades** | Quem nunca fez a inspeção segue o cronograma por bairro ou município do Anexo I da IN 113. Em 49 localidades, a regra do art. 1º da IN 136/2025 dá uma data-fim e a tabela republicada no Anexo da mesma IN dá outra. Exemplo: Madureira, 22/03/2026 pela tabela e 23/09/2026 pela regra. Há ainda 3 localidades no Anexo da IN 136 que não constam do original. |
| **O Inmetro continua acreditando** | A Cgcre mantém a categoria OIA-IG, com escopo que cita a NBR 15923, a IN 113/2024 e a Lei 6.890. Na consulta pública de 10/11/2026, **61 dos 91 organismos OIA-IG** registrados foram acreditados depois de 16/01/2024. A dúvida sobre a validade dessas inspeções, portanto, não é teórica. |

Outros pontos que a leitura trouxe:

- **Laudo reprovado.** A lei (art. 4º) manda interromper o fornecimento imediatamente. A IN 113 (art. 7º) manda a concessionária "avaliar a necessidade". A IN 48 fixa até 15 dias úteis, ou corte imediato quando há escapamento de gás.
- **Contagem.** O prazo corre da inspeção mais recente (IN 113, art. 8º).

## 3. A pergunta do fiscal

> A unidade residencial ou comercial com fornecimento ativo de gás canalizado da CEG ou da CEG RIO tem inspeção de segurança válida dentro do prazo e, se a última inspeção a reprovou, a concessionária interrompeu o fornecimento no prazo regulamentar?

## 4. A regra

```
SE a unidade não é residencial nem comercial, ou não tem fornecimento ativo (L9)
  ENTÃO fora do escopo.
Inspeção válida = realizada entre 21/03/2015 e a data de referência, por quem,
  NA DATA DA INSPEÇÃO, estava acreditado pelo Inmetro como OIA-IG (L1, L2, L10)
  ou credenciado pela concessionária da unidade (L3), com registro em dia no
  CREA, no CAU ou no CRT a partir de 16/01/2024 (IN 113, art. 2º, IV).
Data-limite =
  última inspeção válida + 5 anos (L4, L7); OU, se não houver,
  vistoria prévia da concessionária + 5 anos (L5); OU, se não houver,
  data-fim do cronograma da localidade (L6); OU, fora do Anexo, 22/03/2026.
SE a data de referência passou da data-limite
  ENTÃO NÃO CONFORME (inspeção vencida ou primeira inspeção não realizada).
SENÃO SE a última inspeção reprovou a instalação, ou o prazo de adequação venceu
  sem nova inspeção, E o fornecimento não foi interrompido no prazo
  (imediato com escapamento; senão, 15 dias úteis) (L8, L11)
  ENTÃO NÃO CONFORME (obrigação da concessionária).
SENÃO SE o resultado depende de uma lacuna ainda não decidida
  ENTÃO PRECISA DE DELIBERAÇÃO.
SENÃO CONFORME.
```

A mesma regra está no campo `teste_auditoria.regra` do [`contrato.yaml`](contrato.yaml).

## 5. Classificação: parcialmente computável

A periodicidade, a habilitação na data e a interrupção podem ser computadas, desde que as lacunas da seção 6 recebam um valor. Há duas coisas que nenhum dado estruturado resolve:

- a **qualidade técnica** do laudo (o teste de monóxido foi feito de verdade?);
- a **autenticidade** do documento.

Ambas exigem amostragem e fiscalização em campo, ou um laudo eletrônico assinado.

O arquivo [`verificador/exercicio_autovistoria.py`](verificador/exercicio_autovistoria.py) mostra o que acontece quando se computa **só o texto citado**, sem ler as fontes. A regra fica com três saídas (CONFORME, NÃO CONFORME e PRECISA DE DELIBERAÇÃO), e a terceira aparece sempre que o texto não decide. Exemplos: a vistoria cai na faixa em que "5 anos" muda de sentido, ou a empresa era credenciada só na data da vistoria, ou só hoje.

## 6. Lacunas e parâmetros

Toda lacuna vira parâmetro, com um valor padrão provisório e a indicação de quem decide. O motor completo lê os parâmetros de [`verificador/parametros.json`](verificador/parametros.json); a versão didática ([`regra_autovistoria.py`](verificador/regra_autovistoria.py)) os chama de P1 a P8. Cada veredito informa quais lacunas o influenciaram, o que permite medir quantas unidades dependem de cada decisão pendente.

| Id | Lacuna | Parâmetro | Padrão provisório | Quem decide |
|---|---|---|---|---|
| L1 | OIA acreditado pelo Inmetro **após** a IN 113, sem credenciamento na concessionária, faz inspeção válida? | `oia_inmetro_apos_in113` (P1) | sim (`todos`) | Conselho Diretor |
| L2 | De 21/03 a 31/05/2015, a IN 47 não nomeia quem habilita | `habilitacao_aceita_antes_in113` | exige OIA do Inmetro | Conselho Diretor |
| L3 | Credenciada pela CEG vale para unidade da CEG RIO, e vice-versa? | `credenciamento_vale_para_outra_concessionaria` (P2) | não | Conselho Diretor |
| L4 | Como contar "5 anos" | `contagem_prazo` (P4) | data de aniversário, sem tolerância | CAENE |
| L5 | A vistoria prévia da ligação nova inicia a contagem? | `vistoria_previa_inicia_contagem` (P5) | sim | Conselho Diretor |
| L6 | Cronograma: regra do art. 1º × tabela publicada (49 localidades) | `cronograma_prevalece` (P6) | tabela | Conselho Diretor |
| L7 | A inspeção que reprovou cumpre a periodicidade? | `resultados_que_contam_como_inspecao` (P3) | sim | Conselho Diretor |
| L8 | Interrupção após reprovação: obrigatória (lei) ou avaliada (IN 113)? | `interrupcao_obrigatoria_apos_reprovacao` (P8) | obrigatória | Procuradoria |
| L9 | Unidade suspensa ou desligada continua obrigada? | `incluir_unidades_sem_fornecimento` (P7) | não | Conselho Diretor |
| L10 | A consulta pública da Cgcre não mostra suspensões já encerradas | — (limite de dado) | acreditado da concessão até a suspensão ou o cancelamento | ofício à Cgcre |
| L11 | Os 15 dias úteis contam do recebimento do laudo, data que não era coletada | `prazo_interrupcao_dias_uteis` + campo `data_recebimento_laudo` | conta da data da inspeção, sem feriados | CAENE |
| L12 | Lei estadual de 02/07/2026 que amplia quem pode inspecionar (número e texto não localizados) | — | não incorporada | confirmar no DOERJ |
| L13 | Critério técnico (RIP ou ABNT) muda o conteúdo do laudo, não a periodicidade | — (campo `criterio_tecnico` coletado) | fora do teste | — |

As decisões que mais mudam o resultado são a **L6** (cronograma) e a **L1** (Inmetro × concessionária). Os testes em [`verificador/test_autovistoria.py`](verificador/test_autovistoria.py) trocam o valor de cada uma e conferem o efeito.

## 7. Dados mínimos e quem detém

| Dado | Quem detém | Como chega à AGENERSA |
|---|---|---|
| Unidades residenciais e comerciais, com endereço, classe e situação do fornecimento | concessionária (cadastro comercial e faturamento) | bloco `unidades` |
| Laudos de autovistoria recebidos desde 21/03/2015, com inspetora, responsável técnico e resultado | concessionária (registro de laudos, IN 113, art. 2º, XI); o conteúdo vem do laudo emitido pela inspetora | bloco `inspecoes` |
| Interrupções de fornecimento ligadas à inspeção | concessionária (ordens de serviço) | bloco `interrupcoes` |
| Inspetoras credenciadas pela concessionária, com vigência | concessionária (cadastro de credenciamento, IN 113, art. 2º, I) | bloco `inspetoras_credenciadas` |
| Organismos OIA-IG acreditados, com data de concessão e situação | Cgcre/Inmetro | consulta pública ([`baixar_oia_inmetro.py`](verificador/baixar_oia_inmetro.py)); o histórico de situação pede ofício (L10) |
| Cronograma da primeira inspeção por localidade | AGENERSA (Anexo I da IN 113 e alterações) | [`extrair_cronograma.py`](verificador/extrair_cronograma.py) → [`dados/cronograma_ipg.csv`](verificador/dados/cronograma_ipg.csv) |
| Decisão sobre as lacunas L1 a L12 | AGENERSA | `parametros.json` |

Para cada campo, o `contrato.yaml` registra a origem (quem detém o dado), o tipo, o domínio, a obrigatoriedade e um exemplo. O contrato não pede nome nem CPF do consumidor. Os CPFs que podem aparecer são de inspetores pessoas físicas e de responsáveis técnicos, no exercício da atividade profissional. A base legal é o cumprimento de obrigação legal e regulatória (LGPD, art. 7º, II).

## 8. Três canais, um contrato

O conteúdo é o mesmo nos três canais; muda só o meio de transporte. Todos são gerados a partir do `contrato.yaml`.

| | API | Planilha Excel | Arquivo JSON |
|---|---|---|---|
| Como funciona | o regulado publica a API e a agência consulta | o regulado preenche o modelo e entrega | o regulado gera o arquivo e entrega |
| Esforço de TI do regulado | maior: desenvolvimento, hospedagem e segurança | menor | intermediário |
| Risco de erro de formato | baixo (contrato tipado) | maior (zeros à esquerda, datas como texto) | baixo (schema) |
| Melhor para | integração definitiva e frequente | carga inicial, piloto, baixo volume | integração automatizada sem expor um serviço |

Recomendação para este caso:

1. Começar pelo **JSON**, que é automatizável e não exige expor um serviço.
2. Usar o **Excel** na carga inicial ou num piloto, enquanto o JSON é desenvolvido.
3. Migrar para a **API** se a agência passar a consultar os dados com frequência maior que a mensal.

Periodicidade proposta, a confirmar pela AGENERSA:

- **carga inicial:** `COMPLETA`, com o histórico desde 2015-03-21, em até 60 dias da notificação;
- **envios regulares:** mensais, com `data_referencia` no último dia do mês, até o dia 10 do mês seguinte;
- **reenvio de lote rejeitado:** em até 5 dias úteis.

## 9. Como rodar

Todos os comandos partem da raiz do repositório.

**Gerar os padrões de coleta e validar os envios de exemplo:**

```bash
pip install -r ferramentas/requirements.txt

python ferramentas/gerar_padrao.py exemplos/ipg-gas-rj/contrato.yaml --saida exemplos/ipg-gas-rj/gerado

python ferramentas/validar_envio.py exemplos/ipg-gas-rj/contrato.yaml exemplos/ipg-gas-rj/envios/exemplo_envio_completo.json
python ferramentas/validar_envio.py exemplos/ipg-gas-rj/contrato.yaml exemplos/ipg-gas-rj/envios/exemplo_envio_incremental.json
```

A pasta `gerado/` não é versionada: cada um a gera localmente. Os envios de exemplo devem ser aceitos, isto é, sem nenhuma regra de rejeição violada. O incremental gera um alerta A02 esperado: a inspetora do laudo novo foi informada num envio anterior, e por isso não está no bloco `inspetoras_credenciadas` deste incremento. Na carga `INCREMENTAL`, as regras A02 e A03 (e a R03) são conferidas pela agência contra a base acumulada.

**Rodar o verificador:**

```bash
# testes (só biblioteca padrão + pytest)
python -m pytest exemplos/ipg-gas-rj -q

# exemplo com 13 unidades fictícias, na data-base de 10/11/2026
python exemplos/ipg-gas-rj/verificador/autovistoria.py --data-base 2026-11-10

# versão didática (P1–P8) e versão "só o texto" (três saídas)
python exemplos/ipg-gas-rj/verificador/regra_autovistoria.py
python exemplos/ipg-gas-rj/verificador/exercicio_autovistoria.py

# do envio validado ao veredito
python exemplos/ipg-gas-rj/verificador/json_para_verificador.py exemplos/ipg-gas-rj/envios/exemplo_envio_completo.json saida/ipg
python exemplos/ipg-gas-rj/verificador/autovistoria.py --pasta saida/ipg --data-base 2026-10-31
```

No envio completo de exemplo, o verificador encontra duas unidades com inspeção vencida cujos laudos anteriores a 2024 foram feitos por inspetoras **só credenciadas pela concessionária**. Antes da IN 113, o regime era o da IN 48/2015, que exige acreditação pelo Inmetro. Esse tipo de achado precisa ser confirmado com a agência antes de virar autuação, e é por isso que cada veredito lista as inspeções desconsideradas e o motivo.

**Atualizar os dados públicos** (opcional; os resultados acima não dependem disso):

```bash
# lista OIA-IG da Cgcre/Inmetro -> verificador/dados/oia_inmetro.csv (não versionado)
python exemplos/ipg-gas-rj/verificador/baixar_oia_inmetro.py
python exemplos/ipg-gas-rj/verificador/autovistoria.py --data-base 2026-11-10 \
       --oia exemplos/ipg-gas-rj/verificador/dados/oia_inmetro.csv

# cronograma da 1ª inspeção a partir do texto consolidado da IN 113/2024
# baixe o PDF oficial em:
#   https://www.rj.gov.br/agenersa/sites/default/files/arquivos_paginas_basicas/IN113_0.pdf
pip install pypdf
python exemplos/ipg-gas-rj/verificador/extrair_cronograma.py IN113_0.pdf
```

O `extrair_cronograma.py` regrava `verificador/dados/cronograma_ipg.csv` (173 localidades). Em seguida, lista as 49 divergências entre regra e tabela e as 3 localidades que só aparecem no Anexo da IN 136. O script também aceita um `.txt` já extraído do PDF, com uma linha `--- página N ---` entre as páginas. O texto da norma não é versionado neste repositório.

## 10. Dados fictícios

Todas as unidades, laudos, inspetoras, responsáveis técnicos, CNPJs, CPFs, números de acreditação e endereços dos envios e do verificador são **fictícios**. Os CNPJs e CPFs têm dígito verificador válido, para exercitar a regra R07, e os nomes seguem o padrão "Inspetora Exemplo Ltda.". O CNPJ do remetente nos envios também é fictício. Os únicos nomes reais são os que as normas públicas citam (AGENERSA, CEG, CEG RIO, Inmetro/Cgcre) e o número agregado de organismos OIA-IG da consulta pública.

## 11. Pendências para a versão 1.1 do contrato

Sugestões que não alteram a versão 1.0 e dependem de decisão da AGENERSA:

1. Campo `alterado_em` por registro, para conferir a carga incremental.
2. Forma de informar exclusões e laudos anulados na carga incremental.
3. Exigir `id_inspecao_origem` só para `REPROVACAO` e `ADEQUACAO_NAO_REALIZADA`, já que uma interrupção por `RISCO_IMEDIATO` ou `OUTRO` pode não ter laudo de origem.
4. Novos alertas:
   - `id_inspecao_origem` inexistente em `inspecoes`;
   - inspeção feita por credenciada fora do seu período de credenciamento;
   - `tipo_pessoa` incoerente com o tamanho do documento.
5. Formato `OIA-XX-NNNN` para `numero_acreditacao_inmetro` e `responsavel_envio` separado em nome e e-mail.
