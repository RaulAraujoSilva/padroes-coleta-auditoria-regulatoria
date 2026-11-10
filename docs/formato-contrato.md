# Formato do contrato de coleta (`contrato.yaml`) — versão 1

O contrato de coleta é um arquivo YAML que descreve, num lugar só:

1. o **teste de auditoria** que a agência quer automatizar (pergunta, regra, classificação, lacunas);
2. os **dados** de que o teste precisa (blocos, campos, tipos, domínios, obrigatoriedade);
3. **quem detém** cada dado hoje;
4. as **regras de recebimento** (o que rejeita e o que só alerta).

A partir dele, as ferramentas do repositório geram os padrões de coleta: JSON Schema, modelo Excel, especificação OpenAPI, dicionário de dados e validador.

## Estrutura

```yaml
contrato: ipg-envio                 # identificador, minúsculas e hífen
versao: "1.0"                       # versão do layout, MAIOR.MENOR (MAIOR = mudança incompatível)
titulo: Inspeção Periódica de Gás   # nome curto
descricao: >                        # finalidade da coleta
  ...
orgao: AGENERSA                     # agência que define o padrão
regulados: [CEG, CEG_RIO]           # quem envia (vira o domínio do campo `remetente`)

base_normativa:                     # normas que fundamentam o teste
  - id: LEI-6890-2014
    descricao: Lei Estadual RJ nº 6.890/2014
    url: https://...                # opcional

teste_auditoria:
  pergunta: >                       # pergunta de sim/não do fiscal
    ...
  regra: |                          # regra em português: SE ... ENTÃO ... SENÃO ...
    SE ...
  classificacao: parcialmente_computavel   # computavel | parcialmente_computavel | discricionaria
  saidas: [CONFORME, NAO_CONFORME, PRECISA_DE_DELIBERACAO]
  lacunas:                          # trechos que impedem a automação total
    - id: L1
      trecho: "credenciada pelo Inmetro"
      problema: ...
      decisao_padrao: ...
      quem_decide: Conselho Diretor
      # opcionais (documentação; as ferramentas não os interpretam):
      tipo: conflito_entre_normas   # ver metodo/02-regra-e-lacunas.md
      alternativas: [...]
      situacao: pendente            # pendente | decidida
      ato_decisorio: ...            # deliberação que decidiu, quando houver

periodicidade:
  carga_inicial: "histórico desde 2015-03-21"
  regular: mensal                   # diaria | semanal | mensal | trimestral | anual | sob_demanda
  prazo_entrega: "até o dia 10 do mês seguinte"

cabecalho:                          # campos do envio, além dos automáticos (ver abaixo)
  - nome: responsavel_envio
    tipo: texto
    obrigatorio: true
    descricao: ...

blocos:
  - nome: unidades                  # snake_case; vira aba do Excel, endpoint e propriedade do JSON
    descricao: ...
    chave: [id_unidade]             # unicidade dentro do envio
    campos:
      - nome: id_unidade
        tipo: texto                 # ver tipos abaixo
        obrigatorio: true           # true | false | condição (ver abaixo)
        descricao: ...
        origem: cadastro comercial do regulado   # quem detém o dado hoje
        exemplo: "1000234567"
        tamanho_max: 30             # opcional (texto)
        formato: "^[0-9]{8}$"       # opcional: expressão regular (texto)
        dominio: [A, B]             # obrigatório quando tipo = enum
        referencia: unidades.id_unidade   # opcional: integridade referencial (R03)
        evento: true                # opcional: data de fato já ocorrido; não pode passar da data de referência (R04)
        minimo: 0                   # opcional: inteiro/decimal
        maximo: 100                 # opcional: inteiro/decimal

regras:                             # regras adicionais, além das automáticas
  - id: R06
    tipo: ordem_datas               # ordem_datas | data_minima | condicional | expressao
    severidade: rejeicao            # rejeicao | alerta
    bloco: inspecoes
    antes: data_inspecao
    depois: data_recebimento_laudo
    mensagem: "data_recebimento_laudo deve ser igual ou posterior a data_inspecao"
  - id: A01
    tipo: data_minima
    severidade: alerta
    bloco: inspecoes
    campo: data_inspecao
    valor: "2015-03-21"
    mensagem: "inspeção anterior à vigência da lei"
  - id: A05
    tipo: condicional               # SE a condição `se` vale no registro, ENTÃO a condição `entao` deve valer
    severidade: rejeicao
    bloco: inspecoes
    se: {campo: resultado, igual: REPROVADO}
    entao: {campo: escapamento_gas, preenchido: true}
    mensagem: "laudo reprovado deve informar se houve escapamento"
  - id: A03
    tipo: expressao                 # condição em Python restrito sobre o registro `r` e o envio `e`
    severidade: alerta
    bloco: inspecoes
    condicao: "r['resultado'] != 'REPROVADO' or any(i.get('id_inspecao_origem') == r['id_inspecao'] for i in e['interrupcoes'])"
    mensagem: "laudo reprovado sem interrupção registrada"
```

## Tipos de campo

| tipo | JSON | Excel | Validação |
|---|---|---|---|
| `texto` | string | texto | `tamanho_max`, `formato` |
| `inteiro` | integer | número inteiro | `minimo`, `maximo` |
| `decimal` | number | número | `minimo`, `maximo` |
| `data` | string `AAAA-MM-DD` | data | data real |
| `data_hora` | string ISO 8601 com fuso | texto | ISO 8601 |
| `booleano` | boolean | lista `SIM`/`NAO` | — |
| `enum` | string | lista suspensa | `dominio` |
| `cnpj` | string 14 dígitos | texto | dígito verificador |
| `cpf` | string 11 dígitos | texto | dígito verificador |
| `cpf_cnpj` | string 11 ou 14 dígitos | texto | dígito verificador |
| `cep` | string 8 dígitos | texto | formato |
| `ibge_municipio` | string 7 dígitos | texto | formato |
| `url` | string URI | texto | formato |
| `sha256` | string 64 hex | texto | formato |

## Obrigatoriedade condicional

`obrigatorio` aceita `true`, `false` ou um objeto de condição sobre outro campo do mesmo registro:

```yaml
obrigatorio:
  se: resultado            # campo do mesmo registro
  igual: APROVADO_COM_RESTRICAO     # ou: diferente: X | em: [X, Y] | preenchido: true
```

## Cabeçalho automático

Todo envio tem, além dos campos de `cabecalho`, estes campos gerados pelas ferramentas:

| campo | tipo | descrição |
|---|---|---|
| `contrato` | texto | igual a `contrato` |
| `versao_layout` | texto | igual a `versao` |
| `remetente` | enum (`regulados`) | quem envia |
| `cnpj_remetente` | cnpj | CNPJ de quem envia |
| `data_referencia` | data | data de corte |
| `tipo_carga` | enum `COMPLETA`/`INCREMENTAL` | |
| `data_referencia_anterior` | data | obrigatória se `INCREMENTAL` |
| `gerado_em` | data_hora | |
| `totais` | objeto | contagem por bloco |

## Regras automáticas (não precisam ser escritas)

| id | regra | origem no contrato |
|---|---|---|
| R01 | obrigatórios presentes; tipo, formato e domínio corretos | `campos` |
| R02 | chave única dentro do bloco | `chave` |
| R03 | referência existe no bloco referenciado (só na carga `COMPLETA`) | `referencia` |
| R04 | datas de evento ≤ `data_referencia`; no cabeçalho, `data_referencia_anterior` < `data_referencia` | `evento: true` (tipos `data` e `data_hora`) |
| R05 | obrigatoriedade condicional | `obrigatorio: {se: ...}` |
| R07 | dígito verificador de CNPJ e CPF | tipos `cnpj`, `cpf`, `cpf_cnpj` |
| R08 | `totais` do cabeçalho = contagem real | automático |

Os ids R06 e R09 em diante, e A01 em diante, ficam livres para as `regras` do contrato. Cada id é único no contrato.

Limitações da versão 1 do formato:
- as `regras` sempre se referem a um `bloco`, e não há regra customizada sobre o cabeçalho;
- `ordem_datas` compara datas do mesmo registro, e comparações entre blocos usam `expressao`;
- nas expressões, `r` é o registro e `e` é o envio inteiro (`e['envio']`, `e['<bloco>']`).

## Formato do envio (JSON)

```json
{
  "envio":   { "contrato": "...", "versao_layout": "1.0", "remetente": "...", "...": "...", "totais": {"unidades": 7} },
  "unidades": [ { "id_unidade": "..." } ],
  "inspecoes": [ ]
}
```

O Excel tem uma aba `envio` (campo/valor) e uma aba por bloco, com cabeçalho igual aos nomes dos campos. A API expõe `GET /envios/{data_referencia}` e `GET /<bloco>` para cada bloco, com paginação por cursor.
