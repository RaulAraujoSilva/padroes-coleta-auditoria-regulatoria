# Etapa 1 — Da norma ao teste

**Objetivo:** sair de uma frase como "o regulado deve fazer X a cada N anos (Lei tal, Resolução tal)" e chegar a uma **pergunta de sim ou não** que o fiscal consegue responder para cada caso, com base na **norma vigente**.

**Quem conduz:** fiscalização. **Quem participa:** procuradoria.

**Produto:** seções 1 e 2 da [ficha do teste de auditoria](../modelos/ficha-teste-auditoria.md).

---

## 1.1 Desconfie da regra que chegou pronta

A regra costuma chegar resumida num parágrafo, com uma lista de normas entre parênteses. Esse resumo é útil como ponto de partida, mas frequentemente está desatualizado:

- a norma citada foi **alterada** depois, e o resumo não acompanhou;
- uma norma posterior **mudou quem faz o quê** (por exemplo, quem credencia um terceiro) sem revogar expressamente a anterior;
- o prazo foi **prorrogado** por norma transitória ou por cronograma em anexo;
- o resumo mistura o que diz a lei com o que diz o regulamento, e os dois não coincidem.

No caso que deu origem a este método, a regra recebida dizia que o serviço devia ser executado por "empresa credenciada pelo órgão federal de acreditação". A lei, porém, falava apenas em "empresas credenciadas", sem dizer por quem; quem nomeava o órgão federal era uma instrução normativa de 2015; e uma instrução normativa de 2024 transferiu o credenciamento para as próprias concessionárias, sem revogar a de 2015. A pergunta "a empresa é acreditada?" estava, portanto, incompleta.

**Regra prática:** antes de escrever qualquer teste, leia o texto integral de cada norma citada, e não apenas a ementa ou o resumo.

## 1.2 Localize a versão vigente

Para cada norma citada:

1. **Obtenha o texto oficial**, preferencialmente a publicação no diário oficial e, quando existir, o texto compilado mantido pelo próprio órgão emissor.
2. **Confira se o texto compilado está atualizado.** Compilações oficiais às vezes atrasam. Compare a data da última alteração registrada com a lista de normas posteriores (passo 1.3).
3. **Anote a data de vigência**, que pode ser diferente da data de publicação (vacatio legis, vigência escalonada, dispositivos com vigência própria).
4. **Leia os anexos.** Tabelas, cronogramas e fórmulas costumam estar em anexo e são justamente o que o teste vai usar.

## 1.3 Mapeie a cadeia de alterações e revogações

Monte uma tabela com todas as normas que tocam a obrigação, em ordem cronológica:

| Norma | Publicação | Vigência | O que faz em relação à obrigação | Revoga ou altera expressamente | Observação |
|---|---|---|---|---|---|
| Lei nº [___] | [data] | [data] | cria a obrigação e a sanção | — | |
| Resolução nº [___] | [data] | [data] | regulamenta: define quem executa e o prazo | — | |
| Resolução nº [___] | [data] | [data] | muda quem credencia | revoga a Res. [___] | **não revoga** a Res. [___] |
| Resolução nº [___] | [data] | [data] | prorroga cronograma | altera o Anexo I | republica o Anexo |

Para montar a cadeia:

- procure normas posteriores que **citem** a norma original (busca pelo número no diário oficial e na base normativa da agência);
- procure normas posteriores sobre o **mesmo assunto**, mesmo que não citem a original: é aí que aparecem os conflitos sem revogação expressa;
- verifique **termos de ajustamento de conduta, decisões judiciais e deliberações do colegiado** que tenham alterado a aplicação da norma;
- procure **normas de outros órgãos** que o teste depende (conselhos profissionais, órgãos de acreditação, normas técnicas citadas);
- verifique se há **lei nova em tramitação ou recém-publicada** sobre o tema. No caso de origem, uma lei estadual publicada meses antes ampliava quem podia executar o serviço, e a regra recebida não a mencionava.

### Três situações que exigem atenção

**Conflito sem revogação expressa.** Duas normas em vigor dizem coisas diferentes sobre o mesmo ponto. Não resolva o conflito por conta própria no teste: registre como lacuna do tipo "conflito entre normas" (ver [Etapa 2](02-regra-e-lacunas.md)), com a leitura que parece mais defensável como valor padrão e a procuradoria como responsável pela análise.

**Anexo republicado que contradiz o texto.** Uma norma de alteração pode trazer, no artigo, uma regra geral ("prazos vencidos até tal data passam para tal data") e, no anexo, uma tabela republicada com datas que não seguem essa regra. No caso de origem, isso ocorreu em dezenas de localidades de um cronograma. Registre as divergências uma a uma e trate como lacuna do tipo "anexo × texto".

**Hierarquia normativa.** Quando a lei e o regulamento divergem (por exemplo, a lei manda interromper o serviço imediatamente e o regulamento manda "avaliar a necessidade"), o valor padrão provisório deve seguir a norma hierarquicamente superior, e a lacuna vai à procuradoria.

## 1.4 Identifique o dispositivo exato

Para cada elemento da obrigação, anote o dispositivo (artigo, parágrafo, inciso, item do anexo) que o fundamenta:

| Elemento | Pergunta | Dispositivo |
|---|---|---|
| Sujeito obrigado | quem deve cumprir? | |
| Objeto | o que deve ser feito? | |
| Universo | sobre quais unidades, contratos, ativos ou usuários? | |
| Prazo ou periodicidade | quando? a cada quanto tempo? contado de quando? | |
| Condição de validade | o que torna o cumprimento válido (quem executa, com que habilitação, com que conteúdo)? | |
| Exceções | quem está dispensado? | |
| Consequência | o que acontece se não cumprir? quem sofre a consequência? | |
| Obrigação de registro | o regulado é obrigado a manter registro disso? | |

A última linha é importante para a [Etapa 3](03-dados-minimos.md): se a norma obriga o regulado a manter o registro, pedir o dado é exigir algo que ele já deveria ter.

## 1.5 Escreva a pergunta do fiscal

A pergunta deve:

- ser respondível com **sim ou não** para **um caso** (uma unidade, um contrato, um pedido, um período);
- indicar a **data de referência** da verificação;
- usar os termos da norma vigente, não os do resumo.

| Pergunta ruim | Por quê | Pergunta melhor |
|---|---|---|
| "A concessionária cumpre a norma de inspeções?" | não é por caso, não diz qual norma | "Na data de referência, a unidade U tem inspeção válida realizada há no máximo 5 anos ou, se nunca foi inspecionada, ainda está dentro do prazo do cronograma da sua localidade?" |
| "As reclamações são respondidas no prazo?" | não define prazo nem contagem | "A reclamação R, registrada em D, foi respondida em até N dias úteis contados do registro?" |
| "O indicador está bom?" | "bom" não é critério | "O indicador I do conjunto C no período P ficou dentro do limite L fixado para C em P?" |

Uma obrigação complexa costuma se desdobrar em **várias perguntas encadeadas**. No caso de origem, a pergunta principal se desdobrou em cinco etapas: a unidade está no escopo? quem executou estava habilitado na data? a inspeção está no prazo? a adequação exigida foi feita? o serviço foi interrompido quando devia? Cada uma é um teste próprio, com suas lacunas e seus dados.

## 1.6 Valide com a área técnica

Antes de passar à Etapa 2, apresente à área técnica responsável:

- a cadeia de normas (1.3);
- a redação proposta da regra, em linguagem corrente, com os fundamentos;
- a pergunta (ou perguntas) do fiscal;
- a lista preliminar de pontos duvidosos.

O objetivo não é resolver as dúvidas agora, e sim confirmar que a leitura das normas está completa e que a pergunta corresponde ao que a fiscalização de fato quer verificar.

## Lista de verificação da etapa

- [ ] Texto integral de todas as normas citadas, com anexos.
- [ ] Data de vigência de cada norma e de cada dispositivo relevante.
- [ ] Tabela da cadeia de alterações e revogações.
- [ ] Busca por normas posteriores sobre o mesmo assunto, mesmo sem citação.
- [ ] Busca por normas de outros órgãos de que o teste depende.
- [ ] Conflitos sem revogação expressa anotados.
- [ ] Divergências entre anexo e texto anotadas, uma a uma.
- [ ] Dispositivo exato de cada elemento da obrigação (1.4).
- [ ] Pergunta (ou perguntas) de sim ou não, por caso, com data de referência.
- [ ] Leitura validada com a área técnica.
