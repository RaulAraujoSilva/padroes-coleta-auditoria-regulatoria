# Ferramentas

Gerador de padrões de coleta e validador de envios, em Python, a partir do `contrato.yaml` descrito em [`docs/formato-contrato.md`](../docs/formato-contrato.md).

## Instalação

Requer Python 3.10 ou mais recente.

```bash
pip install -r ferramentas/requirements.txt
# sem permissão de administrador:
pip install --user -r ferramentas/requirements.txt
```

Dependências: `pyyaml`, `openpyxl` e `jsonschema`. O `openapi-spec-validator` é opcional e só é usado nos testes.

## Uso

### 1. Conferir o contrato

```bash
python ferramentas/contrato.py exemplos/ipg-gas-rj/contrato.yaml
```

A ferramenta lista **todos** os problemas de uma vez. Ela confere:
- estrutura e tipos conhecidos;
- `dominio` nos campos `enum`;
- `referencia` apontando para `bloco.campo` existente;
- campos de `chave` existentes;
- condições de obrigatoriedade válidas;
- `exemplo` coerente com o tipo;
- ids de regra únicos e fora dos reservados (R01–R05, R07, R08);
- expressões seguras.

Também emite avisos para pontos que não impedem o uso, como campo sem `origem` ou chave desconhecida.

### 2. Gerar os padrões

```bash
python ferramentas/gerar_padrao.py exemplos/ipg-gas-rj/contrato.yaml --saida exemplos/ipg-gas-rj/gerado
```

| Arquivo | Conteúdo |
|---|---|
| `<contrato>-<versao>.schema.json` | JSON Schema 2020-12 do envio. Tem `$defs` `Envio`, `Totais` e um por bloco, com `additionalProperties: false`, `enum`, `pattern`, `format` e limites. A obrigatoriedade condicional é escrita como `if/then`, inclusive `INCREMENTAL → data_referencia_anterior`. |
| `modelo_<contrato>_v<versao>.xlsx` | Planilha-modelo. Abas: `LEIA-ME`, `envio` (campo/valor, linhas `totais.<bloco>` e coluna de conferência com fórmula), uma aba por bloco como Tabela do Excel, `dicionario` e `listas` (oculta). Os cabeçalhos são coloridos (azul: obrigatório; laranja: condicional; cinza: opcional) e trazem uma nota com descrição, tipo, domínio e origem. A validação de dados usa listas para `enum` e SIM/NAO, data, comprimento para CNPJ/CPF/CEP/IBGE/SHA-256 e faixas numéricas. Os painéis ficam congelados. |
| `openapi.yaml` | OpenAPI 3.1 no modelo *pull*: o regulado expõe e a agência consulta. Usa servidor fictício (`*.exemplo.invalid`) e OAuth2 *client credentials*. Expõe `GET /envios/{data_referencia}` e `GET /<bloco>` com `data_referencia`, `alterado_desde`, `limite` e `cursor`. A resposta tem o formato `{dados, proximo_cursor, total}`, e os erros seguem a RFC 9457 (`application/problem+json`). Os schemas são os mesmos do JSON Schema. |
| `dicionario_de_dados.md` | Teste de auditoria (pergunta, regra, classificação, base normativa e lacunas). Uma tabela por bloco com campo, tipo, obrigatório, domínio/formato, descrição e origem. Por fim, as regras automáticas e as do contrato. |
| `exemplo_envio.json` | Envio sintético (carga COMPLETA, 3 registros por bloco) montado a partir dos `exemplo` dos campos. Respeita chaves, referências e totais e é conferido pelo validador ao final da geração. |

Códigos de saída:
- `0`: tudo gerado e exemplo aceito;
- `1`: artefatos gerados, mas o exemplo foi rejeitado (revise os `exemplo` do contrato);
- `2`: contrato inválido ou erro de uso (nada é gerado).

### 3. Validar um envio

```bash
python ferramentas/validar_envio.py contrato.yaml envio.json
python ferramentas/validar_envio.py contrato.yaml envio.json.gz --json --saida relatorio.json
python ferramentas/validar_envio.py contrato.yaml envio.zip
python ferramentas/validar_envio.py contrato.yaml planilha_preenchida.xlsx --exportar-json envio.json
```

- **Formatos aceitos.** O envio pode chegar em `.json`, `.json.gz`, `.zip` ou `.xlsx`:
  - um `.zip` com vários `.json` é tratado como **partes** do mesmo envio, com cabeçalho idêntico, e as regras valem sobre a união das partes;
  - um `.zip` pode trazer, no lugar dos `.json`, uma única planilha.
- **Validação.** O JSON Schema é gerado em memória a partir do contrato, e o validador aplica depois as regras automáticas e as do contrato.
- **Relatório.** As ocorrências são agrupadas por regra e indicam bloco, chave do registro e campo. No Excel, indicam também a célula, por exemplo `fiscalizacoes!G3`. O relatório traz ainda o SHA-256 do arquivo recebido.
- **Códigos de saída:**
  - `0`: aceito, com ou sem alertas;
  - `1`: rejeitado;
  - `2`: erro de uso, como contrato inválido, arquivo inexistente ou extensão não suportada.

| Regra | O que confere |
|---|---|
| ARQ | arquivo legível: UTF-8, JSON bem-formado, planilha com a aba `envio` e partes compatíveis |
| R01 | obrigatórios presentes; tipo, formato, domínio e limites corretos; nenhum campo fora do layout |
| R02 | chave única dentro do bloco |
| R03 | referência existe no bloco referenciado (só na carga COMPLETA) |
| R04 | datas de `evento: true` ≤ `data_referencia`; `data_referencia_anterior` < `data_referencia` |
| R05 | obrigatoriedade condicional, inclusive `data_referencia_anterior` na carga INCREMENTAL |
| R07 | dígito verificador de CNPJ e CPF |
| R08 | `totais` do cabeçalho = contagem real |
| regras do contrato | `ordem_datas`, `data_minima`, `condicional` e `expressao`, com a severidade definida no contrato |

**Conversão do Excel** (`excel_para_json.py`, também usável sozinho): usa o mesmo contrato e não rejeita nada sozinha. O que não puder ser convertido segue como está, para o validador apontar a célula.

| Situação na planilha | Tratamento |
|---|---|
| célula vazia | campo omitido |
| SIM/NAO | `true`/`false` |
| célula de data | `AAAA-MM-DD` |
| data digitada como `DD/MM/AAAA` | convertida, com aviso |
| `-`, `N/A`, `NA`, `N/D`, `NULL` | tratados como vazio, com aviso |
| fórmula | usa o valor calculado gravado pelo Excel, com aviso; sem valor calculado, campo omitido |
| CNPJ/CPF/CEP com pontuação | pontuação removida, com aviso |
| número digitado como texto | convertido, com aviso |
| `contrato`, `versao_layout`, `gerado_em` ou `totais.<bloco>` vazios | preenchidos pela ferramenta, com aviso |

## Regras `expressao`

A `condicao` é uma expressão Python que deve ser **verdadeira** para cada registro do `bloco`. Se ela for falsa, a regra é violada.

- **Variáveis.** `r` é o registro; um campo ausente vale `None`, então `r['x']` não dá erro. `e` é o envio inteiro (`e['envio']` e `e['<bloco>']`).
- **Funções permitidas.** `any`, `all`, `len`, `min`, `max`, `sum`, `set`, `str`, `int`, `float` e `bool`. Comparações, compreensões, geradores e métodos como `r.get(...)` e `str.startswith(...)` também são aceitos.
- **Proibido.** Lambda, nomes ou atributos iniciados por `_` e qualquer outro nome além dos citados. Essas construções são recusadas já na carga do contrato.
- **Erro na avaliação.** Se a expressão levantar erro durante a avaliação, isso conta como ocorrência da própria regra, com a mensagem do erro.

## Decisões sobre pontos não definidos na especificação

1. **Formato da regra `condicional`** (a especificação não o define):
   ```yaml
   - id: R09
     tipo: condicional
     severidade: rejeicao
     bloco: fiscalizacoes
     se:    {campo: resultado, igual: AUTUADO}        # operadores: igual | diferente | em | preenchido
     entao: {campo: prazo_dias, preenchido: true}
     mensagem: "..."
   ```
   A regra é violada quando `se` é verdadeiro e `entao` é falso. Os operadores são os mesmos da obrigatoriedade condicional, com `campo:` no lugar de `se:`.
2. **Semântica dos operadores.**
   - `igual`, `diferente` e `em` só são verdadeiros quando o campo da condição está preenchido. Assim, `diferente: X` com o campo vazio **não** torna outro campo obrigatório.
   - `preenchido: false` é verdadeiro quando o campo está ausente ou nulo.
3. **`bloco` nas regras.** É opcional; o padrão é `envio`, que aplica a regra ao cabeçalho, com `r` igual ao cabeçalho.
4. **Campos opcionais aceitam `null` no JSON**, tratado como "sem informação". Campos obrigatórios não aceitam `null`, e texto vazio (`""`) é sempre recusado (R01).
5. **Classificação dos erros de obrigatoriedade.**
   - **R05 para `data_referencia_anterior`:** a falta dela na carga INCREMENTAL é obrigatoriedade condicional e, por isso, é classificada como R05.
   - **R04 para a ordem das datas de referência:** `data_referencia_anterior` ≥ `data_referencia` é classificado como R04, por ser uma data em relação à data de referência.
6. **CNPJ ou CPF com DV errado** é R07. Fora do formato, como tamanho errado ou com pontuação no JSON, é R01.
7. **Sem `minItems`.** Os blocos são listas obrigatórias, mas podem vir vazias. A carga COMPLETA não exige registros, porque o contrato não diz quais blocos devem ter dados.
8. **Funções nas expressões.** `bool` foi acrescentada à lista de funções permitidas, porque o caso-exemplo a usa e ela não oferece risco.
9. **Ids de regra.**
   - Só são aceitos ids no padrão `R` ou `A` seguido de dois ou mais dígitos, fora dos reservados.
   - A severidade é a declarada no contrato. Id `A..` com `rejeicao`, ou `R..` com `alerta`, gera apenas aviso.
10. **Chaves desconhecidas no YAML** geram aviso, não erro, para que extensões locais do contrato não quebrem as ferramentas. Também são avisos:
    - campo sem `exemplo`, `descricao` ou `origem`;
    - chave formada por campo não obrigatório.
11. **`exemplo` inválido é erro**, por exemplo fora do domínio, com DV errado ou fora do `formato`. Ele alimenta o envio de exemplo e os `examples` do schema.
12. **`formato` e `tamanho_max` só valem para `texto`.** Os demais tipos já têm formato próprio.
13. **Nomes reservados.** `envio` e `totais` não podem ser nomes de bloco, e campos de `cabecalho` não podem repetir os do cabeçalho automático.
14. **`data_hora` exige fuso horário**, como `-03:00` ou `Z`. No Excel, deve ser digitada como texto; uma célula de data e hora sem fuso é rejeitada.
15. **Referência ao próprio bloco** (por exemplo, `inspecoes.id_inspecao_origem → inspecoes.id_inspecao`) é permitida. Só a auto-referência ao mesmo campo é proibida.
16. **`$id` do schema** é uma URN (`urn:padrao-coleta:<contrato>:<versao>`), para não sugerir um domínio real.

## Limitações conhecidas

- **Envio de exemplo heurístico.** O envio de exemplo pode ser rejeitado quando:
  - o contrato tem regras `expressao` ou `condicional` de rejeição que dependem de combinações de valores;
  - campos de `formato` restrito não têm `exemplo` (o valor genérico pode não casar).

  Nesses casos o gerador avisa e sai com código 1.
- **R03 em carga INCREMENTAL.** A R03 não é aplicada a envios INCREMENTAL isolados, porque depende do histórico acumulado. O relatório registra a observação.
- **Validação de dados do Excel.** Ela orienta quem digita, mas não impede colar valores inválidos. A validação definitiva é a do `validar_envio.py`.
- **Fórmulas sem valor calculado.** Em planilhas criadas por programas que não gravam o valor calculado das fórmulas, o campo é omitido (com aviso).
- **Expressões lentas.** As expressões rodam com `eval` restrito: sem builtins perigosos e sem acesso a atributos internos. Mesmo assim, uma expressão pode ser lenta em envios grandes, por exemplo um `any(...)` sobre outro bloco para cada registro. Prefira expressões simples.
- **OpenAPI sem servidor real.** A especificação descreve só a interface. Autenticação mútua (mTLS), limites de taxa e o endereço real devem ser acertados com cada regulado.

## Testes

```bash
python -m pytest -q ferramentas
```

O contrato `tests/contrato_minimo.yaml` tem 2 blocos e cobre:
- enum;
- referência;
- evento;
- obrigatoriedade condicional;
- uma regra de cada tipo.

Os testes cobrem:
- a recusa de contratos com erro;
- a geração dos artefatos, com o schema conferido por `check_schema` e o OpenAPI por `openapi-spec-validator`;
- a aceitação do exemplo gerado;
- a rejeição de um caso por regra automática e por tipo de regra do contrato;
- a ida e volta pelo Excel;
- a integração com o caso `exemplos/ipg-gas-rj`.
