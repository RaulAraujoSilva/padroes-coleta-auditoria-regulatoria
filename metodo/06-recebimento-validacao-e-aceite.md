# Etapa 6 — Recebimento, validação e aceite

**Objetivo:** garantir que cada envio seja conferido de forma objetiva e reproduzível, com critérios claros de rejeição e de alerta, e que o regulado saiba exatamente o que corrigir.

**Quem conduz:** TI da agência. **Quem participa:** fiscalização; TI dos regulados.

**Modelo:** [checklist de homologação](../modelos/checklist-homologacao.md).

---

## 6.1 Rejeição e alerta

Cada regra de validação tem uma severidade:

| Severidade | Efeito | Quando usar |
|---|---|---|
| **Rejeição** (ids `R..`) | o envio inteiro é recusado e deve ser reenviado corrigido | o erro torna o envio inutilizável, incoerente ou impossível de cruzar |
| **Alerta** (ids `A..`) | o envio é aceito; o alerta é registrado e pode exigir justificativa | a situação pode ser legítima, mas merece explicação, ou indica possível não conformidade |

Regras automáticas, que vêm do próprio contrato (ver [`docs/formato-contrato.md`](../docs/formato-contrato.md)):

| id | Regra |
|---|---|
| R01 | campos obrigatórios presentes; tipo, formato e domínio corretos |
| R02 | chave única dentro do bloco |
| R03 | referência existe no bloco referenciado (na carga completa) |
| R04 | datas de evento não posteriores à `data_referencia` |
| R05 | obrigatoriedade condicional |
| R07 | dígito verificador de CNPJ e CPF |
| R08 | `totais` do cabeçalho iguais à contagem real |

Exemplos de regras adicionais:

| Exemplo | Severidade | Por quê |
|---|---|---|
| data de resposta anterior à data de registro | rejeição | incoerência lógica |
| data de religação anterior à data de interrupção | rejeição | incoerência lógica |
| fato anterior à vigência da norma | alerta | pode ser legítimo (histórico), mas não deve ser usado no teste |
| reprovação sem interrupção registrada | alerta | pode ser uma não conformidade, ou a interrupção ainda não ocorreu |
| serviço feito por terceiro que não consta das listas de habilitação | alerta | pode ser não conformidade, ou cadastro desatualizado |
| código de município fora da área de atuação | alerta | erro de cadastro ou unidade fora da concessão |

**Atenção para não confundir validação com fiscalização.** Um alerta que indica possível não conformidade não é veredito: o veredito é do verificador, com as regras e parâmetros do teste. A validação de recebimento só garante que o dado está bem formado e coerente. E o regulado não deve ser induzido a "corrigir" o dado para fazer o alerta desaparecer; deve corrigir apenas o que estiver errado.

## 6.2 Relatório de validação

Todo envio gera um relatório, devolvido ao regulado, com:

- identificação do envio: contrato, versão do layout, remetente, data de referência, tipo de carga, data e hora do recebimento, hash do arquivo;
- resultado: **ACEITO**, **ACEITO COM ALERTAS** ou **REJEITADO**;
- contagem por bloco: declarada nos `totais` e encontrada;
- lista de ocorrências, cada uma com: id da regra, severidade, bloco, linha (ou posição no arquivo), chave do registro, campo, valor encontrado e mensagem;
- resumo por regra (quantas ocorrências de cada uma), para que o regulado ataque as causas e não os sintomas.

O relatório deve ser **reproduzível**: o mesmo arquivo, validado com a mesma versão do validador, gera o mesmo relatório. Registre a versão do validador no relatório.

## 6.3 Integridade: hash

Para envios por arquivo:

1. O regulado calcula o hash SHA-256 do arquivo e o informa no ato da entrega (no ofício de encaminhamento, no portal ou no protocolo).
2. A agência recalcula o hash do arquivo recebido e confere.
3. Se não conferir, o envio é recusado antes da validação de conteúdo.
4. O hash fica registrado junto com o relatório de validação e o arquivo arquivado.

O hash prova, mais tarde, qual foi exatamente o conteúdo enviado, o que é importante se um veredito for contestado.

## 6.4 Prazos de reenvio

- Envio rejeitado: reenvio corrigido em prazo curto e fixo, por exemplo **5 dias úteis** a partir da comunicação do relatório.
- Alerta que exige justificativa: justificativa no mesmo prazo ou junto com o envio seguinte.
- Rejeições repetidas no mesmo ponto: reunião técnica com o regulado; se o problema for do contrato (campo ambíguo, domínio incompleto), corrija o contrato em nova versão.
- O descumprimento reiterado dos prazos de envio é, ele próprio, matéria de fiscalização, conforme o instrumento normativo ([Etapa 7](07-governanca-e-lgpd.md)).

## 6.5 Carga completa e carga incremental

| | `COMPLETA` | `INCREMENTAL` |
|---|---|---|
| Conteúdo | todo o universo e todo o histórico exigido | só o que foi criado ou alterado desde a `data_referencia_anterior` |
| Volume | maior | menor |
| Validação de referências (R03) | no próprio envio | contra a base acumulada da agência |
| `totais` | contam todos os registros | contam só o incremento |
| Risco | arquivos grandes | registros perdidos; exclusões não comunicadas; dependência de envios anteriores |

Recomendações:

- **A carga inicial é sempre completa.**
- **Prefira cargas completas** enquanto o volume permitir. Elas eliminam o problema de sincronização: cada envio é a fotografia inteira.
- Se usar incremental, defina **como se informam exclusões e anulações** (por exemplo, um campo de situação do registro), exija um campo de **data de alteração** por registro e faça uma **carga completa periódica** (por exemplo, anual) para reconciliar.
- Na carga incremental, regras que dependem de outros registros (referência, cruzamentos) são conferidas pela agência contra a base acumulada, e não pelo validador entregue ao regulado.

## 6.6 Conferência de totais e de consistência entre envios

Além da regra R08 (totais declarados iguais à contagem), a agência deve conferir, a cada envio:

- **variação de volume** em relação ao envio anterior (queda ou salto acima de um limite, por exemplo 10%, gera alerta interno);
- **registros que desapareceram** entre duas cargas completas;
- **registros históricos que mudaram** (datas de fatos antigos alteradas);
- **comparação com fontes independentes**, quando houver (número de unidades informado em outro processo, relatórios anuais).

Essas conferências não rejeitam o envio, mas devem ser explicadas pelo regulado quando significativas.

## 6.7 Homologação antes da produção

Antes de o envio regular começar a valer para fins de fiscalização, cada regulado passa por **homologação**:

1. **Envio de teste com dados reais de um recorte** (um município, um período). Dados fictícios não revelam os problemas reais de cadastro.
2. **Validação** pelo validador, com relatório devolvido.
3. **Correções** até o envio ser aceito sem rejeições.
4. **Conferência por amostragem**: a fiscalização sorteia registros e confere com documentos de origem (laudos, protocolos, ordens de serviço).
5. **Execução do verificador** com o recorte, para confirmar que os dados permitem responder à pergunta do teste.
6. **Carga inicial completa**, validada.
7. **Termo de homologação**, registrando canal, versão do layout, responsável técnico e data a partir da qual os envios regulares são exigíveis.

Use o [checklist de homologação](../modelos/checklist-homologacao.md).

## 6.8 Critérios de aceite de cada envio

Um envio regular é aceito quando:

1. o hash informado confere com o arquivo recebido (envios por arquivo);
2. a versão do layout declarada é uma versão aceita naquele momento;
3. não há nenhuma ocorrência de regra de rejeição;
4. os `totais` conferem com a contagem dos blocos;
5. os alertas que exigem justificativa estão justificados, ou o prazo para justificar está correndo;
6. o envio chegou no prazo, ou o atraso está registrado.

O aceite do envio **não significa** que o regulado está em conformidade com a obrigação fiscalizada. Significa apenas que os dados foram recebidos em condições de ser verificados.

## Lista de verificação da etapa

- [ ] Regras de rejeição e de alerta definidas no contrato, com mensagens claras.
- [ ] Relatório de validação reproduzível, com versão do validador.
- [ ] Conferência de hash para envios por arquivo.
- [ ] Prazos de reenvio e de justificativa definidos.
- [ ] Política de carga completa e incremental definida, incluindo exclusões.
- [ ] Conferências de volume e de consistência entre envios.
- [ ] Homologação com dados reais, amostragem e execução do verificador.
- [ ] Critérios de aceite comunicados aos regulados.
