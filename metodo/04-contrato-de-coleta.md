# Etapa 4 — Contrato de coleta

**Objetivo:** registrar, num único arquivo `contrato.yaml`, o teste de auditoria, os dados, quem os detém e as regras de recebimento. As ferramentas do repositório geram, a partir dele, o JSON Schema, o modelo Excel, a especificação da API, o dicionário de dados e o validador.

**Quem conduz:** TI da agência. **Quem participa:** fiscalização, que valida o conteúdo.

**Produto:** `contrato.yaml`, a partir do [modelo comentado](../modelos/contrato-modelo.yaml).

**Especificação de referência:** [`docs/formato-contrato.md`](../docs/formato-contrato.md). Em caso de dúvida, vale o que está na especificação.

---

## 4.1 Por que um contrato único

O mesmo conteúdo pode chegar à agência por planilha, por arquivo JSON ou por API ([Etapa 5](05-canais-de-envio.md)). Se cada canal tiver sua própria descrição, elas divergem com o tempo: um campo muda de nome na planilha, um domínio ganha um valor na API. O contrato único evita isso: **os canais são gerados a partir dele**, e qualquer mudança passa por uma nova versão.

O contrato também é o documento que acompanha o ofício ao regulado: é a especificação técnica do que se pede.

## 4.2 Passo a passo

### Passo 1 — Identificação

```yaml
contrato: reclamacoes-prazo       # minúsculas e hífen; não muda entre versões
versao: "1.0"                     # sempre entre aspas
titulo: Prazo de atendimento a reclamações
descricao: >
  Finalidade da coleta, em uma ou duas frases.
orgao: AGENCIA_EXEMPLO
regulados: [DISTRIBUIDORA_A, DISTRIBUIDORA_B]
```

- `contrato` é o identificador permanente. Não o altere ao mudar de versão.
- `versao` vai entre aspas para que `1.10` não seja lido como o número `1.1`.
- `regulados` vira a lista fechada do campo `remetente` no cabeçalho de cada envio. Use códigos curtos, em maiúsculas, sem acento.

### Passo 2 — Base normativa

Liste as normas da cadeia levantada na [Etapa 1](01-da-norma-ao-teste.md), inclusive as que alteram ou conflitam com a principal. Cada uma com `id` estável, `descricao` e, se houver, `url` oficial.

### Passo 3 — Teste de auditoria

Transcreva da ficha do teste ([Etapa 2](02-regra-e-lacunas.md)):

- `pergunta`: a pergunta de sim ou não do fiscal;
- `regra`: o texto SE / ENTÃO / SENÃO;
- `classificacao`: `computavel`, `parcialmente_computavel` ou `discricionaria`;
- `saidas`: normalmente `[CONFORME, NAO_CONFORME, PRECISA_DE_DELIBERACAO]`;
- `lacunas`: uma entrada por lacuna, com `id`, `trecho`, `problema`, `decisao_padrao` e `quem_decide`.

Os ids das lacunas devem ser os mesmos usados no arquivo de parâmetros do verificador.

### Passo 4 — Periodicidade

```yaml
periodicidade:
  carga_inicial: "histórico desde 2024-01-01"
  regular: mensal          # diaria | semanal | mensal | trimestral | anual | sob_demanda
  prazo_entrega: "até o dia 10 do mês seguinte"
```

A carga inicial cobre o histórico definido na [Etapa 3](03-dados-minimos.md). A periodicidade regular deve ser compatível com o uso: não peça envio diário para um teste que roda uma vez por mês.

### Passo 5 — Cabeçalho

As ferramentas geram automaticamente os campos `contrato`, `versao_layout`, `remetente`, `cnpj_remetente`, `data_referencia`, `tipo_carga`, `data_referencia_anterior`, `gerado_em` e `totais`. **Não os repita** em `cabecalho`. Acrescente apenas o que for específico do contrato, como o responsável técnico pelo envio.

### Passo 6 — Blocos e campos

Para cada bloco definido na Etapa 3:

```yaml
blocos:
  - nome: reclamacoes
    descricao: Uma linha por reclamação registrada.
    chave: [id_reclamacao]
    campos:
      - nome: id_reclamacao
        tipo: texto
        obrigatorio: true
        descricao: Protocolo da reclamação no sistema do regulado.
        origem: sistema de atendimento do regulado
        exemplo: "2026000123456"
        tamanho_max: 30
```

Para cada campo, preencha sempre `nome`, `tipo`, `obrigatorio`, `descricao` e `origem`. Use os demais atributos quando se aplicarem:

| Atributo | Quando usar |
|---|---|
| `exemplo` | sempre que ajudar o regulado a entender o formato |
| `tamanho_max`, `formato` | textos com limite ou padrão conhecido (expressão regular) |
| `dominio` | obrigatório para `tipo: enum` |
| `referencia` | o campo aponta para a chave de outro bloco (`bloco.campo`) |
| `evento: true` | datas de fatos já ocorridos, que não podem ser posteriores à `data_referencia` |
| `minimo`, `maximo` | inteiros e decimais com faixa conhecida |

**Obrigatoriedade condicional.** Quando um campo só é exigido em certa situação, use a forma de condição:

```yaml
obrigatorio:
  se: situacao
  igual: RESPONDIDA        # ou: diferente: X | em: [X, Y] | preenchido: true
```

**`evento: true` só em datas de fatos.** Prazos futuros (data-limite de adequação, vencimento de um compromisso) não levam `evento: true`, porque é natural que sejam posteriores à data de referência.

**`origem` é obrigatório na prática.** A especificação permite omitir, mas o método exige: é a resposta à pergunta "quem detém o dado hoje?" da Etapa 3, e é o que orienta a TI do regulado a encontrar o dado.

### Passo 7 — Regras adicionais

As regras R01 a R05, R07 e R08 são automáticas (obrigatórios, tipos, domínios, chave única, referência, datas de evento, obrigatoriedade condicional, dígito verificador, totais). Escreva em `regras` apenas o que não está coberto:

| Tipo | Uso típico |
|---|---|
| `ordem_datas` | uma data deve ser igual ou posterior a outra no mesmo registro (resposta ≥ registro; religação ≥ interrupção) |
| `data_minima` | datas anteriores a um marco (início de vigência da norma) |
| `condicional` | relação entre campos que não se expressa por obrigatoriedade condicional |
| `expressao` | condição que envolve outros registros do envio (por exemplo, "toda reprovação tem interrupção registrada") |

Use os ids livres: **R06 e R09 em diante** para rejeição; **A01 em diante** para alerta. Escreva a `mensagem` pensando em quem vai corrigir o arquivo: diga o que está errado e qual é o valor esperado.

**Rejeição ou alerta?** Rejeite o que torna o envio inutilizável ou incoerente (data de resposta antes do registro). Alerte o que pode ser legítimo, mas merece explicação (fato anterior à vigência da norma; reprovação sem interrupção registrada). Ver [Etapa 6](06-recebimento-validacao-e-aceite.md).

## 4.3 Convenções obrigatórias

| Item | Convenção | Exemplo |
|---|---|---|
| Codificação | UTF-8 | |
| Nomes de blocos e campos | `snake_case`, minúsculos, sem acento | `data_resposta`, `id_unidade` |
| Datas | ISO 8601 `AAAA-MM-DD` | `2026-11-10` |
| Data e hora | ISO 8601 com fuso | `2026-11-10T14:30:00-03:00` |
| CNPJ, CPF, CEP, código IBGE | **só dígitos**, com zeros à esquerda | `00123456000191`, `01001000` |
| Valores de domínio | **MAIÚSCULAS**, sem acento, com sublinhado | `APROVADO_COM_RESTRICAO`, `NAO_REALIZADA` |
| Booleanos | `true`/`false` no JSON; `SIM`/`NAO` no Excel | |
| Decimais | ponto como separador no JSON; formato numérico nativo no Excel | `1234.56` |
| Campo sem informação | omitido ou `null`; no Excel, célula vazia. **Nunca** `0`, `-` ou `N/A` | |
| Identificadores | estáveis entre envios | o mesmo `id_unidade` em todos os meses |

Evite domínios com valores genéricos demais (`OUTRO`) sem um campo de texto complementar; e evite domínios que misturam conceitos (situação e motivo no mesmo campo).

## 4.4 Versionamento do layout

A versão segue o formato **MAIOR.MENOR**:

| Tipo de mudança | Exemplos | Versão |
|---|---|---|
| **Compatível** (envio da versão anterior continua válido) | novo campo **opcional**; novo bloco opcional; nova regra de **alerta**; correção de descrição | sobe MENOR: `1.0` → `1.1` |
| **Incompatível** (envio da versão anterior pode ser rejeitado) | novo campo obrigatório; campo renomeado ou removido; mudança de tipo; valor removido de domínio; nova regra de **rejeição**; mudança de chave | sobe MAIOR: `1.1` → `2.0` |

Acrescentar um valor a um domínio é compatível para quem envia, mas pode quebrar quem consome. Trate como MENOR e avise os usuários internos.

### Compatibilidade e transição

- Cada envio declara `versao_layout`. A agência valida o envio contra a versão declarada.
- Ao publicar uma versão MAIOR, mantenha a anterior aceita por um **período de transição** (por exemplo, dois ciclos de envio), comunicado por ofício.
- Mantenha um **registro de mudanças** junto ao contrato: versão, data, o que mudou, motivo (deliberação de lacuna, norma nova, erro recorrente no recebimento).
- Não altere uma versão já publicada. Se houver erro, publique a próxima.
- Mudanças motivadas por deliberação de lacuna devem citar o ato que decidiu.

## 4.5 Revisão do contrato

Antes de publicar, confira:

- [ ] O arquivo carrega sem erro num leitor de YAML.
- [ ] Todo campo tem `descricao` e `origem`.
- [ ] Todo campo usado pela regra existe; todo campo do contrato é usado por alguma linha da regra ou por uma regra de validação.
- [ ] Todo `enum` tem `dominio` em maiúsculas.
- [ ] Toda `referencia` aponta para um campo que existe e é chave do bloco referenciado.
- [ ] Datas de fatos têm `evento: true`; prazos futuros não.
- [ ] As chaves dos blocos são estáveis no tempo.
- [ ] Os ids de regras não colidem com os automáticos (R01–R05, R07, R08).
- [ ] As lacunas têm os mesmos ids do arquivo de parâmetros do verificador.
- [ ] As ferramentas do repositório geram os artefatos sem erro.
- [ ] Um exemplo de envio, com dados fictícios, passa no validador.
