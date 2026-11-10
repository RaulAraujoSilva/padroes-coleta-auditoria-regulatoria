# Minuta de ofício — solicitação de adoção do padrão de coleta

> Modelo. Substitua os campos entre colchetes. Ajuste o fundamento jurídico com a procuradoria da agência. Quando o padrão estiver estável, considere consolidá-lo em resolução ou instrução normativa (ver [`metodo/07-governanca-e-lgpd.md`](../metodo/07-governanca-e-lgpd.md)).

---

**[NOME DA AGÊNCIA]**
[Unidade emissora]

Ofício nº [___]/[AAAA]/[SIGLA]

[Cidade], [dia] de [mês] de [ano].

A Sua Senhoria o(a) Senhor(a)
**[Nome do destinatário]**
[Cargo]
**[Razão social do regulado]**
CNPJ: [_______________]
[Endereço]

**Assunto:** Envio periódico de dados para verificação de [nome da obrigação] — adoção do padrão de coleta `[identificador-do-contrato]`, versão [X.Y].

**Referência:** Processo nº [___]

Senhor(a) [cargo],

1. Esta Agência, no exercício da competência de fiscalização que lhe confere [lei de criação / lei setorial, artigo], e com fundamento em [cláusula ___ do contrato de concessão / termo de autorização] e em [norma geral de prestação de informações, se houver], acompanha o cumprimento da obrigação prevista em [norma e dispositivo: por exemplo, art. ___ da Resolução nº ___], com as alterações de [normas posteriores].

2. A [norma ou cláusula] já obriga essa [concessionária/permissionária/autorizatária] a manter registro de [descrever o registro]. Para que a verificação possa ser feita de forma contínua, objetiva e uniforme entre os regulados, solicitamos que esses registros passem a ser enviados a esta Agência conforme o padrão de coleta anexo.

3. **Do conteúdo.** Os dados solicitados, seus formatos e as regras de validação estão descritos no contrato de coleta `[identificador-do-contrato]`, versão [X.Y] (Anexo I), e no dicionário de dados correspondente (Anexo II). Em síntese, compreendem:

   | Bloco | Conteúdo |
   |---|---|
   | [bloco 1] | [descrição] |
   | [bloco 2] | [descrição] |

   O envio deve abranger o **universo completo** dos registros, sem filtros, cabendo a esta Agência aplicar os critérios de escopo.

4. **Dos canais.** Essa empresa poderá escolher um dos seguintes canais, com conteúdo idêntico:
   a) arquivo JSON, conforme o esquema do Anexo III;
   b) planilha Excel, conforme o modelo do Anexo IV;
   c) [API, conforme a especificação do Anexo V — se oferecida].

   A entrega dos arquivos deverá ser feita exclusivamente por [portal autenticado / SFTP / sistema de protocolo eletrônico], acompanhada do resumo criptográfico (hash SHA-256) de cada arquivo.

5. **Do calendário.** Solicitamos a observância dos seguintes prazos, contados do recebimento deste ofício:

   | Etapa | Prazo |
   |---|---|
   | Indicação do canal escolhido e do responsável técnico (nome, cargo, e-mail institucional) | [10] dias |
   | Reunião técnica de esclarecimento | [15] dias |
   | Envio de teste (homologação), com dados reais de [recorte: município, período] | [45] dias |
   | Carga inicial completa, com histórico desde [AAAA-MM-DD] | [60] dias |
   | Envios regulares, com posição do último dia de cada [mês] | até o dia [10] do [mês] seguinte |
   | Reenvio de envio rejeitado pela validação | [5] dias úteis da comunicação |

6. **Da validação.** Cada envio será submetido ao validador disponibilizado por esta Agência (Anexo VI), que essa empresa deverá executar **antes** de cada entrega. Será considerado recebido o envio que não apresentar ocorrência de regra de rejeição. As ocorrências de alerta deverão ser justificadas quando solicitado. O recebimento do envio não implica reconhecimento de conformidade com a obrigação fiscalizada.

7. **Das alterações do padrão.** Alterações no padrão de coleta serão comunicadas com antecedência mínima de [60] dias, com nova versão do contrato. Durante o período de transição, a versão anterior continuará aceita.

8. **Da proteção de dados pessoais.** Os dados solicitados limitam-se ao necessário para a finalidade de fiscalização. [Não são solicitados nome, CPF ou contato de usuários.] [Os CPFs eventualmente informados referem-se a profissionais, no exercício de sua atividade, e são necessários para verificar a habilitação.] O tratamento tem por base o cumprimento de obrigação legal ou regulatória e a execução de competência legal desta Agência (Lei nº 13.709/2018, art. 7º, II, e art. 23). Os dados serão mantidos em ambiente de acesso restrito, pelo prazo de [___], e os resultados somente serão divulgados de forma agregada.

9. **Das consequências.** O não envio, o envio fora do prazo ou o envio de informações incompletas ou inverídicas sujeita essa empresa às sanções previstas em [norma de sanções e dispositivo], sem prejuízo das demais medidas cabíveis.

10. Eventuais dúvidas técnicas poderão ser encaminhadas a [unidade], pelo e-mail [e-mail institucional], com referência ao processo indicado acima.

Atenciosamente,

[Nome]
[Cargo]
[Unidade]

---

**Anexos**

- I — Contrato de coleta `[identificador]`, versão [X.Y] (`contrato.yaml`)
- II — Dicionário de dados
- III — Esquema JSON
- IV — Modelo de planilha Excel
- V — Especificação da API [se aplicável]
- VI — Validador e instruções de uso
- VII — Checklist de homologação
