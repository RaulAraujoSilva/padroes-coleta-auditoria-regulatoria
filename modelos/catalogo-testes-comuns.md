# Catálogo de testes de auditoria comuns em regulação

> Ponto de partida para as Etapas 1 a 3 do método. Cada padrão traz a pergunta típica, a regra esqueleto, as lacunas que costumam aparecer, os dados mínimos com o detentor usual, as saídas e as armadilhas. **Nenhum padrão dispensa a leitura da norma vigente** ([Etapa 1](../metodo/01-da-norma-ao-teste.md)): os esqueletos mostram a forma, não o conteúdo jurídico do seu caso.

| # | Padrão | Setores em que é frequente |
|---|---|---|
| 1 | [Periodicidade de obrigação](#1-periodicidade-de-obrigação) | gás, energia, saneamento, transportes |
| 2 | [Prazo de atendimento](#2-prazo-de-atendimento) | todos |
| 3 | [Habilitação de terceiro na data do fato](#3-habilitação-ou-credenciamento-de-terceiro-na-data-do-fato) | gás, energia, transportes, saneamento |
| 4 | [Limite numérico ou indicador de qualidade](#4-limite-numérico-ou-indicador-de-qualidade) | energia, saneamento, gás, transportes |
| 5 | [Cronograma ou meta de investimento](#5-cumprimento-de-cronograma-ou-meta-de-investimento) | todos os setores concedidos |
| 6 | [Reajuste ou fórmula tarifária](#6-reajuste-ou-fórmula-tarifária) | todos os setores tarifados |
| 7 | [Reincidência para dosimetria](#7-reincidência-para-dosimetria) | todos |
| 8 | [Comunicação obrigatória ao usuário](#8-comunicação-obrigatória-ao-usuário) | energia, saneamento, gás |
| 9 | [Continuidade do serviço](#9-continuidade-do-serviço) | energia, saneamento, gás, transportes |
| 10 | [Cobertura ou universalização](#10-cobertura-ou-universalização) | saneamento, energia, gás |

Saídas: em todos os padrões, `CONFORME`, `NAO_CONFORME` e `PRECISA_DE_DELIBERACAO`. Quando houver estados intermediários (por exemplo, "pendente no prazo"), eles não geram veredito até que o prazo vença.

---

## 1. Periodicidade de obrigação

*Algo deve ser feito a cada N meses ou anos: inspeção, manutenção, calibração, renovação de documento, análise de qualidade.*

**Pergunta típica.** Na data de referência, o item X tem a atividade realizada há no máximo N [anos/meses] ou, se nunca foi realizada, ainda está dentro do prazo da primeira realização?

**Regra esqueleto.**
```
PARA cada item X no universo:
  SE X está fora do escopo ENTÃO não se aplica.
  realizações válidas = realizações de X por executor habilitado na data [padrão 3]
  SE não há realização válida
    SE data_referencia > prazo da primeira realização [cronograma, data de início] ENTÃO NÃO CONFORME
    SENÃO pendente no prazo
  SENÃO data_limite = última realização válida + N, contado conforme CONTAGEM
    SE data_referencia ≤ data_limite ENTÃO CONFORME SENÃO NÃO CONFORME
```

**Lacunas típicas.**
- *Contagem de prazo:* "5 anos" é a data de aniversário, 365 × 5 dias ou até o fim do mês? há tolerância?
- *Marco temporal:* de quando conta a primeira realização (início da operação, vistoria inicial, vigência da norma)?
- *Termo indefinido:* uma realização com resultado negativo (reprovação) conta para a periodicidade?
- *Escopo:* itens desativados, suspensos ou em obra estão obrigados?
- *Anexo × texto:* cronogramas de primeira realização republicados com datas que não seguem o artigo.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| universo de itens, com situação e localização | regulado (cadastro técnico ou comercial) |
| realizações: item, data, executor, resultado | regulado (registro obrigatório) |
| data de início da operação ou da vistoria inicial | regulado |
| cronograma da primeira realização | a própria agência (norma) |

**Armadilhas.** Pedir só "a última realização" impede verificar a cadeia histórica e a habilitação de quem fez. O regulado filtrar o universo pelo seu próprio entendimento do escopo. Esquecer que o cronograma pode variar por localidade.

---

## 2. Prazo de atendimento

*O regulado deve responder, executar ou concluir algo em até N dias de um pedido: reclamação, ligação nova, religação, ressarcimento, reparo.*

**Pergunta típica.** O pedido P, registrado em D, foi atendido em até N [dias úteis/corridos/horas] contados de [marco]?

**Regra esqueleto.**
```
PARA cada pedido P com registro no período:
  SE P fora do escopo (tipo, canal) ENTÃO não se aplica.
  data_limite = marco(P) + N conforme CONTAGEM, acrescida de suspensões admitidas
  SE P não atendido
    SE data_referencia > data_limite ENTÃO NÃO CONFORME SENÃO pendente no prazo
  SENÃO SE data_atendimento ≤ data_limite ENTÃO CONFORME SENÃO NÃO CONFORME
```

**Lacunas típicas.**
- *Contagem de prazo:* dias úteis ou corridos; calendário de feriados (municipal?); horas comerciais.
- *Marco temporal:* registro, protocolo, pagamento de taxa, entrega de documentos pelo usuário?
- *Termo indefinido:* o que é "atendimento" (resposta parcial, agendamento, conclusão)?
- *Consequência discricionária:* prorrogações "mediante justificativa"; suspensão por pendência do usuário.
- *Dado inexistente:* calendário de feriados municipais não consolidado.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| pedido: protocolo, tipo, canal, data e hora de registro, município | regulado (sistema de atendimento) |
| eventos do pedido: suspensões, pendências do usuário, prorrogações, com datas | regulado |
| data e hora do atendimento e tipo (parcial, final) | regulado |
| calendário de feriados | a própria agência (atos oficiais) |

**Armadilhas.** Receber o tempo médio já calculado em vez do registro por pedido. Ignorar suspensões legítimas e gerar falsos NÃO CONFORME. Usar data quando o prazo é em horas. Ver o [contrato-modelo.yaml](contrato-modelo.yaml).

---

## 3. Habilitação ou credenciamento de terceiro na data do fato

*O serviço só é válido se executado por terceiro habilitado: organismo acreditado, empresa credenciada, profissional com registro ativo, laboratório reconhecido.*

**Pergunta típica.** Na data em que o serviço S foi executado, o executor E estava habilitado por alguma das vias admitidas pela norma vigente naquela data?

**Regra esqueleto.**
```
PARA cada serviço S:
  vias admitidas = vias previstas na norma vigente em S.data [cadeia normativa]
  SE algum período de habilitação de E, por via admitida, cobre S.data ENTÃO válido
  SENÃO SE E consta em alguma lista mas sem histórico que cubra S.data ENTÃO PRECISA DE DELIBERAÇÃO
  SENÃO inválido (o serviço não conta para o padrão 1)
```

**Lacunas típicas.**
- *Conflito entre normas:* norma nova muda quem habilita sem revogar a antiga; habilitações anteriores "ficam dispensadas" e as posteriores?
- *Escopo:* habilitação concedida por um regulado vale para serviços na área de outro?
- *Dado inexistente:* lista pública mostra só a situação atual, sem histórico de suspensões e cancelamentos.
- *Marco temporal:* períodos de transição entre regimes de habilitação.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| serviço: data, documento do executor (CNPJ/CPF), responsável técnico e registro profissional | regulado |
| habilitações concedidas pelo regulado, com início e fim | regulado |
| acreditações e seu histórico de situação | órgão de acreditação (a agência busca; histórico por ofício, se não for público) |
| registro profissional ativo | conselho profissional (a agência busca) |

**Armadilhas.** Validar a habilitação **hoje** em vez de na data do fato. Comparar nomes em vez de documentos. Não guardar a versão da lista externa usada em cada verificação. Pedir ao regulado uma lista que é pública.

---

## 4. Limite numérico ou indicador de qualidade

*Um indicador deve ficar dentro de um limite: continuidade, pressão, qualidade da água, perdas, pontualidade, nível de tensão.*

**Pergunta típica.** O indicador I, calculado para o conjunto C no período P, ficou dentro do limite L fixado para C em P?

**Regra esqueleto.**
```
PARA cada conjunto C e período P:
  I = fórmula(eventos ou medições de C em P), com expurgos admitidos
  L = limite vigente para C em P
  SE dados insuficientes (cobertura de medição < mínimo) ENTÃO PRECISA DE DELIBERAÇÃO
  SE I dentro de L ENTÃO CONFORME SENÃO NÃO CONFORME
```

**Lacunas típicas.**
- *Termo indefinido:* critérios de expurgo (força maior, eventos externos, dia crítico).
- *Contagem de prazo:* período de apuração (civil, móvel), arredondamento.
- *Escopo:* conjuntos criados ou alterados no meio do período.
- *Dado inexistente:* amostragem mínima não definida; pontos de medição sem cadastro.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| eventos ou medições elementares, com data, local e duração ou valor | regulado |
| marcação de expurgo e motivo, por evento | regulado |
| cadastro de conjuntos ou pontos de medição, com vigência | regulado |
| limites por conjunto e período | a própria agência |

**Armadilhas.** Receber só o indicador calculado (sem como conferir). Aceitar expurgos sem o motivo por evento. Ignorar mudanças de composição dos conjuntos ao longo do tempo.

---

## 5. Cumprimento de cronograma ou meta de investimento

*Obras, aquisições ou metas físicas e financeiras previstas em contrato, plano ou revisão tarifária.*

**Pergunta típica.** A meta M, prevista para a data D (ou o período P), foi cumprida em quantidade, valor e prazo?

**Regra esqueleto.**
```
PARA cada meta M:
  SE M foi alterada por aditivo ou decisão vigente ENTÃO usar a versão vigente em D
  SE executado(M) ≥ previsto(M) até D ENTÃO CONFORME
  SENÃO SE há pedido de reprogramação pendente ENTÃO PRECISA DE DELIBERAÇÃO
  SENÃO NÃO CONFORME
```

**Lacunas típicas.**
- *Termo indefinido:* quando uma obra está "concluída" (física, energização, operação comercial, transferência ao ativo)?
- *Marco temporal:* reprogramações aprovadas, tácitas ou pendentes.
- *Escopo:* substituição de uma obra por outra equivalente.
- *Consequência discricionária:* tolerâncias percentuais.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| metas previstas, com versão e ato de aprovação | a própria agência (contrato, plano) |
| execução física por meta: marcos e datas | regulado |
| execução financeira por meta, com vínculo ao ativo | regulado (contabilidade regulatória) |
| evidências: termo de recebimento, ordem de serviço | regulado |

**Armadilhas.** Metas sem identificador estável entre plano, execução e contabilidade. Comparar valores nominais de anos diferentes sem atualização. Confundir obra concluída com obra paga.

---

## 6. Reajuste ou fórmula tarifária

*A tarifa aplicada ao usuário deve resultar da fórmula e dos parâmetros homologados.*

**Pergunta típica.** A tarifa aplicada na fatura F, para a categoria C, na data D, é igual à tarifa homologada vigente em D para C, e foi calculada com os índices e parâmetros corretos?

**Regra esqueleto.**
```
PARA cada combinação (categoria C, faixa, data D):
  tarifa_homologada = tabela vigente em D (ato de homologação)
  SE |tarifa_aplicada − tarifa_homologada| ≤ TOLERANCIA_ARREDONDAMENTO ENTÃO CONFORME
  SENÃO NÃO CONFORME
PARA o reajuste:
  recalcular fórmula com índices oficiais do período; comparar com o pleito
```

**Lacunas típicas.**
- *Marco temporal:* faturas com consumo que atravessa a data de reajuste (pro rata?).
- *Contagem de prazo:* índice do mês de referência ou do mês anterior; defasagem de publicação.
- *Termo indefinido:* regras de arredondamento e truncamento.
- *Conflito entre normas:* decisões judiciais ou liminares que suspendem reajustes.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| tabela tarifária homologada, com vigência | a própria agência |
| índices de preços | instituto oficial (a agência busca) |
| faturamento por categoria, faixa e período (ou amostra de faturas) | regulado |
| período de consumo e data de leitura por fatura | regulado |

**Armadilhas.** Pedir faturas com nome e CPF do usuário quando o código da unidade basta. Ignorar consumo pro rata. Não guardar a versão do índice usada (índices podem ser revisados).

---

## 7. Reincidência para dosimetria

*A sanção varia conforme o histórico do infrator: reincidência específica ou genérica, dentro de uma janela de tempo.*

**Pergunta típica.** Na data da infração I, o regulado tinha, nos N anos anteriores, decisão definitiva por infração [da mesma natureza / qualquer natureza]?

**Regra esqueleto.**
```
PARA cada infração I:
  anteriores = penalidades do mesmo regulado com decisão definitiva
               em janela [data(I) − N, data(I)) [marco: data do fato ou da decisão?]
  SE algum anterior com mesmo enquadramento ENTÃO reincidência específica
  SENÃO SE algum anterior ENTÃO reincidência genérica
  SENÃO primário
```

**Lacunas típicas.**
- *Marco temporal:* a janela conta da data do fato, da autuação ou do trânsito em julgado administrativo?
- *Termo indefinido:* "mesma natureza" (mesmo dispositivo, mesmo capítulo, mesmo bem jurídico)?
- *Sujeito obrigado:* sucessão empresarial, grupo econômico, troca de CNPJ.
- *Conflito entre normas:* regulamento de sanções revogado durante a janela.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| processos sancionadores: regulado, dispositivo, data do fato, data da decisão definitiva, sanção | a própria agência (sistema processual) |
| sucessões e alterações societárias | regulado; cadastro nacional de pessoas jurídicas |

**Armadilhas.** É um teste em que **o detentor dos dados é a própria agência**: o problema costuma ser a qualidade do próprio sistema processual (dispositivo infringido em texto livre, datas faltando). Começar pela organização dos dados internos.

---

## 8. Comunicação obrigatória ao usuário

*O regulado deve avisar o usuário com antecedência ou em prazo: interrupção programada, suspensão por inadimplência, reajuste, mudança contratual.*

**Pergunta típica.** Antes do evento E (por exemplo, suspensão do serviço da unidade U), o usuário foi comunicado pelo meio exigido, com antecedência mínima de N dias, e a comunicação continha as informações obrigatórias?

**Regra esqueleto.**
```
PARA cada evento E que exige comunicação:
  comunicações válidas = comunicações a U, por meio admitido, com conteúdo obrigatório [parcial]
  SE nenhuma comunicação válida ENTÃO NÃO CONFORME
  SENÃO SE data(E) − data(comunicação) ≥ N conforme CONTAGEM ENTÃO CONFORME
  SENÃO NÃO CONFORME
```

**Lacunas típicas.**
- *Marco temporal:* conta da emissão, da postagem ou do recebimento da comunicação?
- *Termo indefinido:* meios admitidos (fatura, carta, mensagem eletrônica, aviso público).
- *Escopo:* eventos emergenciais dispensados de aviso.
- *Dado inexistente:* comprovante de entrega não registrado.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| eventos que exigem comunicação: unidade, tipo, data | regulado |
| comunicações: unidade, meio, data de emissão, data de entrega (se houver), modelo usado | regulado |
| modelos de comunicação (texto) | regulado; a agência confere o conteúdo uma vez por modelo |

**Armadilhas.** O conteúdo da comunicação é parcialmente computável: verifique o **modelo** uma vez e, por evento, apenas qual modelo foi usado. Evite pedir telefone ou e-mail do usuário.

---

## 9. Continuidade do serviço

*O serviço não pode ser interrompido além de certos limites, ou deve ser restabelecido em prazo; interrupções devem ser registradas e justificadas.*

**Pergunta típica.** A interrupção I, iniciada em D, foi restabelecida dentro do prazo máximo, e foi registrada com causa e abrangência corretas?

**Regra esqueleto.**
```
PARA cada interrupção I:
  SE I.programada e comunicação prévia exigida ENTÃO aplicar padrão 8
  duração = fim(I) − início(I)
  SE I ainda aberta e data_referencia − início(I) > PRAZO ENTÃO NÃO CONFORME
  SE duração ≤ PRAZO conforme tipo de interrupção ENTÃO CONFORME SENÃO NÃO CONFORME
  SE causa = força maior (expurgo) e sem evidência ENTÃO PRECISA DE DELIBERAÇÃO
```

**Lacunas típicas.**
- *Termo indefinido:* o que é interrupção (queda total, redução de pressão ou tensão abaixo de limite)?
- *Escopo:* duração mínima para registro; interrupções provocadas pelo usuário.
- *Consequência discricionária:* expurgos por força maior.
- *Marco temporal:* início a partir do evento ou da reclamação do primeiro usuário?

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| interrupções: identificador, início e fim (data e hora), tipo (programada ou não), causa, área ou unidades afetadas | regulado (sistema de operação) |
| unidades afetadas por interrupção (ou número) | regulado |
| reclamações de falta de serviço | regulado (cruza com o padrão 2) |

**Armadilhas.** Receber só interrupções que o regulado classificou como relevantes. Datas sem hora e sem fuso. Cruzar com reclamações para detectar interrupções não registradas.

---

## 10. Cobertura ou universalização

*Metas de atendimento a uma população ou área: percentual de domicílios atendidos, ligações em áreas novas, atendimento de pedidos em áreas de expansão obrigatória.*

**Pergunta típica.** No município ou área A, na data D, a cobertura atingiu a meta vigente? Os pedidos de ligação em área de obrigação foram atendidos?

**Regra esqueleto.**
```
PARA cada área A e data D:
  cobertura = unidades atendidas(A, D) / universo de referência(A, D)
  meta = meta vigente para A em D
  SE universo de referência sem fonte definida ENTÃO PRECISA DE DELIBERAÇÃO
  SE cobertura ≥ meta ENTÃO CONFORME SENÃO NÃO CONFORME
PARA cada pedido em área de obrigação: aplicar padrão 2
```

**Lacunas típicas.**
- *Termo indefinido:* o que é "atendido" (rede disponível na porta, ligação ativa, factibilidade)?
- *Dado inexistente:* universo de referência (domicílios) desatualizado entre censos.
- *Escopo:* áreas irregulares, rurais ou de difícil acesso.
- *Marco temporal:* metas intermediárias e reprogramações.

**Dados mínimos e detentor usual.**

| Dado | Detentor usual |
|---|---|
| unidades atendidas por área, com data de ligação e situação | regulado |
| extensão de rede e áreas com rede disponível | regulado (cadastro técnico, geoespacial) |
| universo de referência (domicílios, população) | instituto oficial de estatística (a agência busca); município |
| metas por área e período | a própria agência (contrato, plano) |

**Armadilhas.** Numerador e denominador de fontes com datas diferentes. Receber o percentual já calculado. Áreas geográficas com códigos diferentes entre regulado e fonte oficial: use o código oficial do município.
