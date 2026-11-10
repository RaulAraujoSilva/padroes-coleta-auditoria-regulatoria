# Etapa 7 — Governança e LGPD

**Objetivo:** dar ao padrão de coleta base jurídica, calendário, responsáveis e proteção adequada aos dados pessoais, e garantir que ele seja revisto quando a norma ou as decisões mudarem.

**Quem conduz:** procuradoria e diretoria. **Quem participa:** fiscalização; encarregado pelo tratamento de dados pessoais; TI.

**Modelo:** [minuta de ofício de solicitação de dados](../modelos/oficio-solicitacao-dados.md).

> Este texto é orientação técnica e não substitui a análise da procuradoria da agência sobre o caso concreto.

---

## 7.1 Instrumento para exigir o envio

O dever de enviar dados precisa de um fundamento formal. As opções mais comuns, da mais simples à mais robusta:

| Instrumento | Quando usar | Vantagens | Limitações |
|---|---|---|---|
| **Ofício** com base em cláusula contratual ou norma geral de prestação de informações | piloto; poucos regulados; obrigação de registro já existente | rápido; dispensa processo normativo | exigibilidade menor; sanção pelo descumprimento depende da norma em que se apoia; precisa ser renovado a cada mudança relevante |
| **Cláusula contratual** (contrato de concessão, termo aditivo, termo de autorização) | novas concessões; revisões contratuais | vincula o regulado de forma direta | depende de negociação ou de revisão do contrato |
| **Resolução ou instrução normativa** da agência | padrão permanente; muitos regulados; sanção específica pelo descumprimento | maior segurança jurídica; vale para todos; pode prever sanção | exige processo normativo, com análise de impacto e participação pública quando aplicável |

Recomendação prática: começar por **ofício**, apoiado na obrigação de registro e na cláusula de prestação de informações, durante o piloto e a homologação; e consolidar o padrão em **resolução ou instrução normativa** quando ele estiver estável. A norma deve remeter ao contrato de coleta publicado (com sua versão), para que mudanças de layout não exijam nova norma a cada vez, mas apenas comunicação com antecedência mínima.

O instrumento deve conter, no mínimo:

- a finalidade (a obrigação regulatória fiscalizada);
- o fundamento legal e contratual;
- a remissão ao contrato de coleta e à sua versão;
- os canais aceitos;
- o calendário (carga inicial, envios regulares, reenvio);
- as consequências do não envio, do envio fora do prazo e do envio com dados falsos ou incompletos;
- o responsável técnico a ser indicado pelo regulado;
- o tratamento dos dados pessoais.

## 7.2 Calendário

Um calendário típico, contado a partir da notificação:

| Etapa | Prazo indicativo |
|---|---|
| Indicação do canal e do responsável técnico | 10 dias |
| Reunião técnica de esclarecimento | 15 dias |
| Envio de teste (homologação) com dados reais de um recorte | 45 dias |
| Carga inicial completa | 60 dias |
| Envios regulares | conforme `periodicidade` do contrato (por exemplo, até o dia 10 do mês seguinte) |
| Reenvio de envio rejeitado | 5 dias úteis |
| Comunicação de nova versão do layout | antecedência mínima de 60 dias (versão MAIOR) |

Ajuste os prazos ao porte dos regulados e ao volume histórico.

## 7.3 Responsabilidades

| Papel | Responsabilidade |
|---|---|
| Diretoria ou conselho | aprovar o instrumento; decidir as lacunas de sua competência |
| Procuradoria | fundamento jurídico; conflitos entre normas; consequências; LGPD |
| Área de fiscalização | dona do teste: regra, parâmetros, casos de teste, uso dos resultados |
| TI da agência | dona do contrato e das ferramentas: versões, validador, recebimento, guarda |
| Encarregado pelo tratamento de dados pessoais | avaliação de necessidade dos dados pessoais; registro das operações de tratamento; relatório de impacto, quando cabível |
| Regulado: responsável técnico | geração, validação prévia e envio; correções; justificativas de alertas |
| Regulado: área regulatória | interlocução formal; respostas a ofícios |

Formalize esses papéis numa matriz de responsabilidades anexa ao instrumento ou ao processo administrativo.

## 7.4 Dados pessoais: minimização

A Lei Geral de Proteção de Dados Pessoais (LGPD, Lei nº 13.709/2018) exige que o tratamento se limite ao **mínimo necessário** para a finalidade (art. 6º, III). Na prática:

- **Não peça nome, CPF, telefone ou e-mail do usuário final** se o teste pode ser feito com o identificador da unidade ou do contrato e o endereço do imóvel.
- **Endereço de imóvel** é necessário quando a regra varia por localidade ou quando a fiscalização precisa ir a campo. Avalie se o bairro e o município bastam.
- **CPF de profissional** (por exemplo, o responsável técnico que assinou um laudo, ou um inspetor pessoa física) é dado pessoal, mas tratado no contexto da atividade profissional e necessário para verificar a habilitação. Mantenha-o, mas restrinja o acesso.
- **Dados sensíveis** (saúde, por exemplo, em cadastros de usuários com prioridade de atendimento por dependência de equipamento elétrico) só quando indispensáveis à regra, com justificativa expressa e controles reforçados.
- Prefira **identificadores pseudonimizados** quando a agência não precisar reidentificar a pessoa.

Registre, no contrato, a justificativa de cada campo com dado pessoal (no atributo `descricao`).

## 7.5 Base legal

Para a agência reguladora, as bases legais aplicáveis costumam ser:

- **art. 7º, II, da LGPD:** cumprimento de obrigação legal ou regulatória pelo controlador. O regulado entrega os dados porque a norma ou o contrato o obriga; a agência os trata para exercer a fiscalização que a lei lhe atribui.
- **art. 23 da LGPD:** tratamento pelo poder público para o atendimento de sua finalidade pública, na persecução do interesse público, com o objetivo de executar as competências legais ou cumprir as atribuições legais do serviço público. O art. 23 exige que o órgão informe as hipóteses em que trata dados pessoais, com a previsão legal, a finalidade, os procedimentos e as práticas utilizadas, em veículo de fácil acesso, preferencialmente em seu sítio eletrônico.

Do lado do regulado, a entrega à agência também se apoia no art. 7º, II (obrigação legal ou regulatória).

Cumpra também a transparência: publique, na página da agência sobre proteção de dados, que essa coleta existe, para que serve e qual a base legal.

## 7.6 Segurança e retenção

- Acesso aos dados recebidos restrito às equipes de fiscalização e TI envolvidas, com registro de acesso.
- Armazenamento cifrado e com cópia de segurança.
- **Prazo de retenção** definido e documentado. Uma referência comum é o maior entre o prazo prescricional da ação punitiva da administração (em geral 5 anos, contados do fato ou da cessação da infração permanente ou continuada, conforme a Lei nº 9.873/1999) e o prazo de guarda previsto na tabela de temporalidade de documentos da agência; acrescido do tempo de eventual processo administrativo ou judicial em curso.
- Arquivos originais recebidos, com hash e relatório de validação, guardados pelo mesmo prazo, como prova do que foi enviado.
- Descarte seguro ao fim do prazo, com registro.
- Incidentes de segurança comunicados conforme o art. 48 da LGPD.

## 7.7 Publicação de resultados

Os resultados do teste interessam à sociedade, mas a publicação deve respeitar a proteção de dados e o devido processo:

- Publique **resultados agregados**: por regulado, por município, por período; percentuais de conformidade; evolução no tempo.
- **Não publique dados no nível da unidade** quando ela puder ser associada a uma pessoa (endereço completo de residência, por exemplo).
- Diferencie, na publicação, os vereditos definitivos dos que dependem de lacunas ainda não decididas (`PRECISA_DE_DELIBERACAO` ou marcados por lacuna).
- Não trate um veredito `NAO_CONFORME` do verificador como infração apurada: ele é o ponto de partida do processo administrativo, com direito de defesa.
- Publique também o **método**: a regra, os parâmetros e as decisões das lacunas. Isso aumenta a previsibilidade e reduz a contestação.

## 7.8 Revisão periódica do padrão

O padrão de coleta envelhece. Programe revisões:

| Gatilho | O que revisar |
|---|---|
| Norma nova ou alteração da norma | Etapa 1 inteira; lacunas superadas; nova versão do contrato |
| Decisão de uma lacuna | parâmetro do verificador; contrato, se a decisão mudar os dados necessários |
| Erros recorrentes no recebimento | definição dos campos, domínios e mensagens; material de orientação |
| Alertas recorrentes | se viraram rotina, avaliar se devem ser regra de rejeição ou se o alerta está mal calibrado |
| Campos nunca usados pelo verificador | retirar na próxima versão MAIOR (minimização) |
| Revisão anual | todo o ciclo: o teste ainda faz sentido? os dados ainda são os mínimos? o canal ainda é o adequado? |

Registre cada revisão no registro de mudanças do contrato, com a data e o motivo.

## Lista de verificação da etapa

- [ ] Instrumento escolhido, com os elementos mínimos (7.1).
- [ ] Calendário definido e comunicado.
- [ ] Matriz de responsabilidades formalizada.
- [ ] Dados pessoais reduzidos ao mínimo, com justificativa por campo.
- [ ] Base legal registrada e transparência ativa publicada.
- [ ] Prazo de retenção e procedimento de descarte definidos.
- [ ] Política de publicação de resultados agregados.
- [ ] Gatilhos e periodicidade de revisão definidos.
