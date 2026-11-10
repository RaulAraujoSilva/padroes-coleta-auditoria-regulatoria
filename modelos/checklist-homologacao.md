# Checklist de homologação do envio

> Use este checklist para homologar o envio de cada regulado antes de os envios regulares passarem a valer para fins de fiscalização. Método: [`metodo/06-recebimento-validacao-e-aceite.md`](../metodo/06-recebimento-validacao-e-aceite.md).

| | |
|---|---|
| **Regulado** | [código do regulado, igual ao domínio `regulados` do contrato] |
| **Contrato e versão** | [`identificador`] / [X.Y] |
| **Canal escolhido** | [ ] arquivo JSON  [ ] planilha Excel  [ ] API (regulado hospeda)  [ ] API (agência hospeda) |
| **Responsável técnico do regulado** | [nome, cargo, e-mail institucional] |
| **Responsável na agência** | [nome, unidade] |
| **Recorte do envio de teste** | [município, período, unidade operacional] |
| **Início / conclusão** | [AAAA-MM-DD] / [AAAA-MM-DD] |

Marque cada item como **OK**, **NÃO** ou **N/A**, e registre observações.

## A. Preparação

| # | Item | Situação | Observação |
|---|---|---|---|
| A1 | Ofício ou instrumento normativo recebido pelo regulado, com data registrada | | |
| A2 | Canal e responsável técnico indicados formalmente | | |
| A3 | Reunião técnica realizada, com ata | | |
| A4 | Regulado recebeu contrato, dicionário, modelos e validador na versão vigente | | |
| A5 | Credenciais individuais de acesso emitidas (portal, SFTP ou API) | | |
| A6 | Regulado confirmou qual identificador do seu sistema é estável para cada chave | | |

## B. Envio de teste — forma

| # | Item | Situação | Observação |
|---|---|---|---|
| B1 | Arquivo entregue pelo canal seguro acordado (não por e-mail aberto ou link público) | | |
| B2 | Hash SHA-256 informado e conferido | | |
| B3 | Codificação UTF-8; acentos legíveis | | |
| B4 | Cabeçalho completo: contrato, versão do layout, remetente, CNPJ, data de referência, tipo de carga, gerado em, totais | | |
| B5 | Versão do layout declarada é a vigente | | |
| B6 | Planilha: abas e colunas com os nomes exatos do modelo, sem colunas ou abas extras | | |
| B7 | Planilha: CNPJ, CPF, CEP e códigos com zeros à esquerda preservados | | |
| B8 | Datas no formato AAAA-MM-DD (JSON) ou como data (Excel), nunca texto em formato local | | |
| B9 | Domínios em maiúsculas, exatamente como no contrato | | |
| B10 | Campos sem informação vazios ou nulos; nenhum `0`, `-` ou `N/A` usado como "sem informação" | | |
| B11 | API: autenticação, cifragem (TLS 1.2 ou superior) e paginação funcionando | | |

## C. Envio de teste — validação

| # | Item | Situação | Observação |
|---|---|---|---|
| C1 | Validador executado pelo regulado antes da entrega (relatório anexado) | | |
| C2 | Validador executado pela agência; resultado idêntico ao do regulado | | |
| C3 | Nenhuma ocorrência de regra de rejeição | | |
| C4 | Totais declarados iguais à contagem real | | |
| C5 | Alertas analisados; justificativas recebidas quando cabíveis | | |
| C6 | Número de rodadas até o aceite: [__] | | |

## D. Envio de teste — conteúdo

| # | Item | Situação | Observação |
|---|---|---|---|
| D1 | Universo completo do recorte enviado, sem filtro de escopo | | |
| D2 | Volume coerente com fontes independentes (relatórios, outros processos) | | |
| D3 | Amostra de [__] registros sorteados conferida com documentos de origem (laudos, protocolos, ordens de serviço) | | |
| D4 | Divergências da amostra registradas e explicadas: [__] de [__] | | |
| D5 | Identificadores estáveis: um segundo envio de teste mantém as mesmas chaves | | |
| D6 | Dados pessoais restritos aos previstos no contrato | | |
| D7 | Datas de fatos coerentes (nenhuma data futura; ordem lógica entre datas) | | |

## E. Uso no teste de auditoria

| # | Item | Situação | Observação |
|---|---|---|---|
| E1 | Verificador executado com os dados do recorte, sem erro | | |
| E2 | Todos os casos receberam uma das três saídas (CONFORME, NAO_CONFORME, PRECISA_DE_DELIBERACAO) | | |
| E3 | Proporção de PRECISA_DE_DELIBERACAO por falta ou incoerência de dado: [__]% (meta: [__]%) | | |
| E4 | Lacunas acionadas contabilizadas por id | | |
| E5 | Amostra de vereditos revisada manualmente pela fiscalização, sem divergência não explicada | | |

## F. Carga inicial completa

| # | Item | Situação | Observação |
|---|---|---|---|
| F1 | Carga `COMPLETA` com todo o histórico exigido entregue no prazo | | |
| F2 | Aceita sem rejeições | | |
| F3 | Referências entre blocos íntegras (R03) | | |
| F4 | Hash conferido e arquivo arquivado com o relatório de validação | | |
| F5 | Verificador executado sobre a carga completa | | |

## G. Conclusão

| # | Item | Situação | Observação |
|---|---|---|---|
| G1 | Todos os itens obrigatórios (A a F) com OK ou N/A justificado | | |
| G2 | Pendências não impeditivas registradas, com prazo | | |
| G3 | Data a partir da qual os envios regulares são exigíveis: [AAAA-MM-DD] | | |
| G4 | Termo de homologação assinado e juntado ao processo | | |

**Resultado:** [ ] HOMOLOGADO  [ ] HOMOLOGADO COM PENDÊNCIAS  [ ] NÃO HOMOLOGADO

Pendências e prazos:

1. [ ]

Responsável na agência: ______________________ Data: ____/____/______

Responsável técnico do regulado: ______________________ Data: ____/____/______
