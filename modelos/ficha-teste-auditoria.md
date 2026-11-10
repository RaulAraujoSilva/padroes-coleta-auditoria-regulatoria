# Ficha do teste de auditoria

> Modelo em branco. Copie este arquivo, dê a ele o nome do teste e preencha cada seção. As instruções em itálico podem ser apagadas depois de preenchidas. Método: [`metodo/`](../metodo/README.md).

| | |
|---|---|
| **Teste** | [nome curto do teste] |
| **Identificador** | [mesmo valor do campo `contrato` no contrato.yaml, ex.: `reclamacoes-prazo`] |
| **Área responsável** | [unidade de fiscalização dona do teste] |
| **Elaborado por / em** | [nome] / [AAAA-MM-DD] |
| **Revisado pela procuradoria em** | [AAAA-MM-DD ou "pendente"] |
| **Versão da ficha** | [1, 2, …] |

---

## 1. Norma

*Etapa 1. Liste toda a cadeia de normas que tocam a obrigação, em ordem cronológica. Leia o texto integral, com anexos. Inclua normas que alteram, prorrogam, conflitam ou dependem de outros órgãos.*

### 1.1 Regra recebida (como chegou)

> [transcreva a frase ou o resumo que motivou o teste, com as normas citadas]

### 1.2 Cadeia normativa

| Norma | Publicação | Vigência | O que faz em relação à obrigação | Revoga ou altera expressamente | Observação (conflito, anexo, pendência) |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

### 1.3 Dispositivos

| Elemento | Dispositivo | Texto (trecho) |
|---|---|---|
| Sujeito obrigado | | |
| Objeto | | |
| Universo | | |
| Prazo ou periodicidade | | |
| Condição de validade | | |
| Exceções | | |
| Consequência | | |
| Obrigação de manter registro | | |

### 1.4 Regra atualizada (redação proposta)

*Reescreva a regra em linguagem corrente, de acordo com a norma vigente, citando os fundamentos.*

> [redação]
> Fundamentos: [normas e dispositivos]

## 2. Pergunta do fiscal

*Uma pergunta de sim ou não, por caso (unidade, contrato, evento, período), com data de referência. Se a obrigação se desdobra, liste as perguntas encadeadas.*

1. [pergunta principal]
2. [pergunta encadeada, se houver]

## 3. Regra (SE / ENTÃO / SENÃO)

*Etapa 2. Uma condição por linha. Ordem: escopo, validade (habilitação na data do fato), tempestividade, consequências. Use os ids das lacunas entre colchetes onde houver dúvida.*

```
PARA cada [caso]:
  SE ...
    ENTÃO ...
    SENÃO ...
```

## 4. Classificação

*Marque uma opção e justifique em uma frase.*

- [ ] `computavel`
- [ ] `parcialmente_computavel`
- [ ] `discricionaria`

Justificativa: [ ]

Fora da automação (pede amostragem, fiscalização em campo ou documento assinado): [ ]

## 5. Lacunas e parâmetros

*Cada ponto duvidoso vira um parâmetro com valor padrão provisório e responsável pela decisão. Tipos: termo indefinido, marco temporal, contagem de prazo, conflito entre normas, anexo × texto, escopo, sujeito obrigado, consequência discricionária, dado inexistente. Nunca deixe sem valor padrão.*

| Id | Tipo | Trecho | Problema | Alternativas (com fundamento) | Valor padrão provisório | Quem decide | Impacto estimado | Situação |
|---|---|---|---|---|---|---|---|---|
| L1 | | "" | | A: … / B: … | | | [preencher após rodar] | PENDENTE |
| L2 | | "" | | | | | | PENDENTE |

## 6. Saídas

*Padrão: `CONFORME`, `NAO_CONFORME`, `PRECISA_DE_DELIBERACAO`. Se o verificador tiver saídas detalhadas (por exemplo, "pendente no prazo", "fora do escopo"), diga a qual das três cada uma corresponde.*

| Saída detalhada | Corresponde a | Quando |
|---|---|---|
| | CONFORME | |
| | NAO_CONFORME | |
| | PRECISA_DE_DELIBERACAO | |

Cada veredito deve trazer: justificativa em linguagem corrente; lacunas acionadas; registros desconsiderados e motivo.

## 7. Dados e detentores

*Etapa 3. Cada dado aponta para a linha da regra que o usa. Dados públicos são buscados pela própria agência.*

| Dado | Linha da regra que usa | Detentor hoje | Base legal da obrigação de manter | Granularidade | Histórico necessário | Chave estável | Dado pessoal? (justificativa) | Pedir ao regulado ou a agência busca? |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |

### 7.1 Blocos

| Bloco | Conteúdo | Chave | Referências |
|---|---|---|---|
| | | | |

### 7.2 Fontes externas

| Fonte | Dado | Tem histórico? | Como obter | Periodicidade de atualização |
|---|---|---|---|---|
| | | | | |

## 8. Casos de teste

*De 5 a 15 casos fictícios. Cubra: caso conforme, caso não conforme, limites de prazo (dia exato, anterior, seguinte), cada lacuna, habilitação válida na data do fato mas não hoje (e o inverso), dado ausente, dado incoerente.*

| # | Descrição | Entradas principais | Data de referência | Saída esperada | Lacunas acionadas |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 9. Encaminhamentos

| Lacuna(s) | Instância | Documento de encaminhamento | Data | Decisão (ato) |
|---|---|---|---|---|
| | | | | |

## 10. Histórico da ficha

| Versão | Data | Alteração | Motivo |
|---|---|---|---|
| 1 | | criação | |
