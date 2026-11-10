# Etapa 2 — Regra e lacunas

**Objetivo:** transformar a pergunta do fiscal numa regra escrita no formato **SE / ENTÃO / SENÃO**, classificar o quanto ela pode ser verificada automaticamente e transformar cada ponto duvidoso num **parâmetro explícito** com dono.

**Quem conduz:** fiscalização. **Quem participa:** procuradoria; diretoria ou conselho, para decidir as lacunas.

**Produto:** seções 3 a 6 da [ficha do teste de auditoria](../modelos/ficha-teste-auditoria.md); bloco `teste_auditoria` do contrato.

---

## 2.1 Escreva a regra em SE / ENTÃO / SENÃO

A regra é escrita em português, sem linguagem de programação, mas com a precisão de um algoritmo. Use:

- **SE** para cada condição verificável com dados;
- **ENTÃO** para a saída quando a condição se confirma;
- **SENÃO** para o caminho alternativo;
- os nomes de **parâmetros** (ver 2.4) no lugar de cada ponto duvidoso.

Exemplo (prazo de resposta a reclamação):

```
PARA cada reclamação R com data de registro dentro do período verificado:
  SE R está fora do escopo (canal ou tipo não abrangido pela norma)
    ENTÃO não se aplica.
  SE R não tem data de resposta
    SE a data de referência > data limite de R
      ENTÃO NÃO CONFORME (sem resposta e prazo vencido)
      SENÃO pendente no prazo (não gera veredito ainda)
  SENÃO
    data limite = data de registro + PRAZO_DIAS contados conforme FORMA_CONTAGEM [lacunas L1, L2]
    SE a data de resposta ≤ data limite
      ENTÃO CONFORME
      SENÃO NÃO CONFORME
  SE algum dado necessário está ausente ou incoerente
    ENTÃO PRECISA DE DELIBERAÇÃO (dado insuficiente)
```

Boas práticas:

- **Uma condição por linha.** Facilita revisar e testar.
- **Ordem das verificações:** escopo primeiro, depois validade do cumprimento (quem executou, com que habilitação), depois tempestividade, depois consequências.
- **Explicite a data de referência** de cada comparação: data do fato, data do registro, data da verificação.
- **Valide habilitações na data do fato.** Um credenciamento válido hoje não prova que o terceiro estava habilitado quando executou o serviço; um credenciamento cancelado hoje não invalida um serviço feito quando ele estava vigente. A regra deve comparar a data do fato com o período de vigência da habilitação.

## 2.2 Três saídas, e nunca chute

Todo teste tem três saídas possíveis:

| Saída | Quando |
|---|---|
| `CONFORME` | os dados mostram que a obrigação foi cumprida, em qualquer leitura razoável da norma |
| `NAO_CONFORME` | os dados mostram que a obrigação foi descumprida, em qualquer leitura razoável da norma |
| `PRECISA_DE_DELIBERACAO` | o resultado depende de uma lacuna ainda não decidida, ou o dado está ausente ou incoerente |

"Nunca chute" significa: se o resultado muda conforme a leitura da norma, o verificador **não escolhe uma leitura silenciosamente**. Há duas formas aceitáveis de tratar isso:

1. **Saída conservadora:** devolver `PRECISA_DE_DELIBERACAO` sempre que o caso cair na faixa em que as leituras divergem. Por exemplo, se "5 anos" pode significar 1.825 ou 1.826 dias, a unidade cuja verificação cai exatamente no dia de diferença vai para deliberação.
2. **Saída com parâmetro registrado:** aplicar o valor padrão provisório do parâmetro e **registrar, no veredito, que aquela lacuna influenciou o resultado**. O veredito continua `CONFORME` ou `NAO_CONFORME`, mas carrega a marca da lacuna.

A segunda forma é a mais útil na prática: permite rodar o verificador desde o primeiro dia e, depois, **medir quantos casos dependem de cada decisão pendente**. Esse número ajuda a priorizar a pauta do colegiado. Antes de qualquer ato sancionador, porém, os vereditos marcados por lacunas não decididas devem ser revistos.

Dados incoerentes (data do fato posterior à data de referência, documento inválido, registro que referencia unidade inexistente) também levam a `PRECISA_DE_DELIBERACAO` no verificador. Na maioria dos casos, eles já serão barrados antes, na validação de recebimento ([Etapa 6](06-recebimento-validacao-e-aceite.md)).

## 2.3 Classifique o teste

| Classificação | Significado | Exemplo |
|---|---|---|
| `computavel` | a regra pode ser verificada inteiramente com dados, sem juízo humano, depois de decididas as lacunas | prazo de resposta em dias, com contagem definida |
| `parcialmente_computavel` | parte da regra é verificável com dados; outra parte exige juízo humano, amostragem ou fiscalização em campo | periodicidade da inspeção é computável; a qualidade técnica do laudo não é |
| `discricionaria` | o núcleo da regra depende de avaliação técnica ou de conveniência e oportunidade | "adotar as medidas adequadas para garantir a segurança" |

Mesmo um teste classificado como `discricionaria` pode se beneficiar de dados: eles servem para **selecionar casos para análise humana** (trilhas de auditoria), e não para emitir veredito automático.

Registre também o que fica **fora da automação por natureza**, por exemplo: a autenticidade de um documento, a qualidade técnica de um serviço, a veracidade de uma declaração. Esses pontos pedem amostragem, fiscalização em campo ou documentos eletrônicos assinados.

## 2.4 Tipologia de lacunas

Uma **lacuna** é qualquer trecho da norma (ou da realidade dos dados) que impede responder à pergunta do fiscal sem uma decisão adicional. A tipologia abaixo cobre a grande maioria dos casos encontrados em regulação.

| Tipo | O que é | Exemplo | Quem costuma decidir |
|---|---|---|---|
| **Termo indefinido** | palavra ou expressão sem definição na norma | "imediatamente", "unidade comercial", "atendimento", "interrupção" | área técnica; colegiado se houver impacto relevante |
| **Marco temporal** | não está claro a partir de quando a obrigação existe ou quando começa a contagem | o prazo da primeira inspeção conta da ligação ou da vistoria prévia? a regra vale para fatos anteriores à norma? | colegiado |
| **Contagem de prazo** | a norma diz "N anos/dias", mas não diz como contar | dias corridos ou úteis? feriados de qual calendário? aniversário, 365 × N ou fim do mês? existe tolerância? | área técnica |
| **Conflito entre normas** | duas normas vigentes dizem coisas diferentes, sem revogação expressa | regulamento antigo exige acreditação federal; regulamento novo aceita credenciamento pelo próprio regulado | procuradoria, depois colegiado |
| **Anexo × texto** | o anexo (tabela, cronograma, fórmula) contradiz o artigo da mesma norma | artigo prorroga "todos os prazos vencidos até X"; tabela republicada traz datas diferentes | colegiado (errata ou consolidação) |
| **Escopo** | não está claro quais casos estão sujeitos à obrigação | unidades suspensas ou desligadas estão obrigadas? áreas comuns de condomínio? | colegiado |
| **Sujeito obrigado** | não está claro quem deve cumprir ou quem responde pelo descumprimento | a obrigação é do usuário ou do concessionário? a sanção recai sobre quem? | procuradoria |
| **Consequência discricionária** | a norma dá margem de escolha sobre a consequência | lei manda interromper; regulamento manda "avaliar a necessidade" de interromper | procuradoria |
| **Dado inexistente** | a regra é clara, mas o dado necessário não existe, não é registrado ou não está acessível | lista pública de acreditados mostra só a situação atual, sem histórico de suspensões; data de recebimento do laudo não é registrada | área técnica (exigir o campo) ou ofício a outro órgão |

Uma mesma lacuna pode ter mais de um tipo. Classifique pelo tipo principal e mencione os demais na descrição.

## 2.5 Transforme cada lacuna em parâmetro

Cada lacuna vira um **parâmetro** com estes atributos:

| Atributo | Conteúdo |
|---|---|
| `id` | identificador curto e estável (L1, L2, …). Nunca reutilize um id. |
| Trecho | o trecho da norma (ou o ponto da regra) que gera a dúvida, entre aspas |
| Tipo | um dos tipos da tabela 2.4 |
| Problema | por que o trecho impede a decisão automática, em uma ou duas frases |
| Alternativas | as leituras possíveis, cada uma com seu fundamento |
| Valor padrão provisório | a leitura adotada enquanto não houver decisão, com a justificativa |
| Quem decide | a instância competente: área técnica, procuradoria, diretoria, conselho, outro órgão |
| Impacto estimado | quantos casos mudam de resultado se o valor mudar (preenchido depois de rodar o verificador) |
| Situação | `PENDENTE`, `DECIDIDA` (com referência ao ato) ou `SUPERADA` (por norma nova) |

Regras para o valor padrão provisório:

1. **Preferir a leitura com melhor fundamento jurídico**, e não a mais conveniente para a fiscalização ou para o regulado.
2. **Em conflito de hierarquia, seguir a norma superior.**
3. **Em conflito entre anexo e texto, escolher uma das duas de forma explícita** e listar os casos divergentes, para que o colegiado veja o tamanho do problema.
4. **Nunca deixar o parâmetro sem valor.** Sem valor padrão, o verificador não roda; com valor padrão marcado, ele roda e informa a dependência.

No contrato de coleta, as lacunas ficam em `teste_auditoria.lacunas`, com `id`, `trecho`, `problema`, `decisao_padrao` e `quem_decide` (ver [Etapa 4](04-contrato-de-coleta.md)). O verificador mantém os mesmos ids num arquivo de parâmetros, que é o único lugar onde os valores são alterados.

## 2.6 O verificador registra as lacunas acionadas

Para cada caso verificado, a saída do verificador deve conter, além do veredito:

- a justificativa em linguagem corrente (datas, prazos, documento do terceiro);
- a lista de **lacunas acionadas**, isto é, os parâmetros cujo valor influenciou o resultado;
- os registros desconsiderados e o motivo (por exemplo, inspeção feita por terceiro não habilitado na data).

Com isso, a agência consegue responder a perguntas como "se o conselho decidir a lacuna L1 no sentido contrário, quantas unidades mudam de conforme para não conforme?" sem refazer a análise.

Para que isso funcione, o verificador deve ter **testes automatizados que trocam o valor de cada parâmetro** e conferem que o resultado muda como esperado.

## 2.7 Encaminhe para deliberação

Prepare uma nota curta para cada instância decisória, agrupando as lacunas de sua competência:

1. resumo do teste e por que ele importa;
2. para cada lacuna: trecho, alternativas com fundamentos, valor padrão adotado, impacto estimado;
3. pedido objetivo: "decidir entre as alternativas A e B" ou "editar errata do Anexo I".

Priorize as lacunas pelo impacto medido. No caso de origem, de treze lacunas, duas (o conflito sobre quem pode executar o serviço e o cronograma contraditório) respondiam pela maior parte dos resultados em aberto.

Quando a decisão sair, atualize o parâmetro, marque a lacuna como `DECIDIDA` com a referência do ato e, se a decisão alterar o conteúdo da coleta, abra uma nova versão do contrato.

## 2.8 Escreva casos de teste

Antes de passar à Etapa 3, escreva de 5 a 15 **casos de teste** fictícios, cada um com entradas e saída esperada, cobrindo:

- um caso claramente conforme e um claramente não conforme;
- os limites de prazo (o dia exato do vencimento, o dia anterior e o seguinte);
- cada lacuna, com o caso que cai na faixa de dúvida;
- habilitação válida na data do fato mas não hoje, e o inverso;
- dado ausente e dado incoerente.

Esses casos servem para validar a regra com a área técnica agora e para testar o verificador depois.

## Lista de verificação da etapa

- [ ] Regra em SE / ENTÃO / SENÃO, uma condição por linha.
- [ ] Habilitações e condições de validade avaliadas na data do fato.
- [ ] Classificação do teste e o que fica fora da automação.
- [ ] Cada lacuna com tipo, trecho, alternativas, valor padrão, quem decide.
- [ ] Nenhum parâmetro sem valor padrão.
- [ ] Notas de encaminhamento para cada instância decisória.
- [ ] Casos de teste com saída esperada, incluindo os de cada lacuna.
