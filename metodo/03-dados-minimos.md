# Etapa 3 — Dados mínimos

**Objetivo:** derivar da regra a lista **mínima** de dados necessários, identificar **quem detém** cada um hoje e com que **base legal** ele pode ser exigido.

**Quem conduz:** fiscalização. **Quem participa:** TI da agência; encarregado pelo tratamento de dados pessoais.

**Produto:** seção 7 da [ficha do teste de auditoria](../modelos/ficha-teste-auditoria.md); esboço dos `blocos` do contrato.

---

## 3.1 Derive os dados da regra, linha por linha

Percorra a regra escrita na [Etapa 2](02-regra-e-lacunas.md). Para cada condição SE, pergunte: **que dado preciso para avaliar esta condição?**

| Linha da regra | Dado necessário | Observação |
|---|---|---|
| "SE a unidade está no escopo" | classe de consumo; situação do fornecimento | escopo depende da lacuna de escopo |
| "SE o terceiro estava habilitado na data" | documento do terceiro; data do fato; período de vigência da habilitação | validação na data |
| "SE a data do fato + prazo ≥ data de referência" | data do fato | forma de contagem é parâmetro |
| "SE o serviço foi interrompido" | data da interrupção; vínculo com o fato que a motivou | |

Depois, acrescente apenas:

- a **chave** de cada registro (identificador estável);
- os dados de **localização** necessários para regras que variam por região (por exemplo, cronograma por município);
- os dados necessários para **resolver lacunas** do tipo "dado inexistente" (por exemplo, a data de recebimento de um documento, quando o prazo conta dela);
- dados de **controle** que ajudam a validar o envio (por exemplo, hash de um documento, data de alteração do registro).

**O que não entra:** dado "que pode ser útil um dia", dado que nenhuma linha da regra usa, dado pessoal que não altera o veredito. Cada campo do contrato deve poder apontar para a linha da regra que o usa.

## 3.2 Para cada dado, responda seis perguntas

| Pergunta | Por que importa |
|---|---|
| **1. Quem detém o dado hoje?** | define a quem pedir (regulado, terceiro, outro órgão, a própria agência) |
| **2. Qual a base legal que obriga o detentor a mantê-lo?** | sustenta a exigência; se não há obrigação de registro, talvez seja preciso criá-la antes |
| **3. Qual a granularidade necessária?** | por unidade? por evento? por mês? agregado demais impede o teste; detalhado demais aumenta custo e risco |
| **4. Qual o histórico necessário?** | desde quando? a regra olha para trás N anos? há prazo prescricional? |
| **5. Qual é a chave estável?** | o mesmo identificador precisa aparecer em todos os envios, para cruzar e acompanhar no tempo |
| **6. O dado contém informação pessoal?** | se sim, ele é indispensável? há alternativa menos invasiva? (ver [Etapa 7](07-governanca-e-lgpd.md)) |

Registre as respostas numa tabela por dado. Ela vira, quase diretamente, os atributos `descricao`, `origem` e `obrigatorio` de cada campo no contrato.

### Granularidade

Prefira o **registro do evento** (cada inspeção, cada reclamação, cada interrupção) ao indicador já calculado. Com o evento, a agência calcula o indicador, confere o cálculo do regulado e muda a regra sem pedir dado novo. Peça indicador agregado apenas quando o volume de eventos for desproporcional ao benefício ou quando a norma definir a obrigação diretamente sobre o agregado.

### Histórico

A carga inicial deve cobrir o período em que a regra pode gerar consequência:

- desde a **vigência** da norma, se a regra olha para todo o histórico (por exemplo, "a última inspeção" pode ter ocorrido há muitos anos);
- ou o **período de verificação** acrescido da **janela da regra** (por exemplo, se o teste é sobre o ano corrente e a periodicidade é de 5 anos, são necessários pelo menos 5 anos anteriores);
- respeitando os prazos prescricionais da ação punitiva.

### Chave estável

Os problemas mais comuns são:

- identificador que **muda quando o cliente muda** (trocar a titularidade gera novo código);
- identificador **reaproveitado** depois de desativado;
- identificador **diferente entre sistemas** do mesmo regulado (comercial × operacional).

Pergunte ao regulado qual código é estável no tempo e, se nenhum for, peça um código de correspondência.

## 3.3 Dados que a própria agência busca

Nem todo dado deve ser pedido ao regulado. **Dados públicos ou mantidos por outros órgãos devem ser obtidos pela própria agência**, diretamente na fonte oficial:

| Exemplo de dado | Fonte usual | Por que não pedir ao regulado |
|---|---|---|
| lista de organismos acreditados e situação da acreditação | órgão federal de acreditação | fonte oficial; o regulado só repetiria, com risco de erro ou desatualização |
| registro profissional ativo | conselhos profissionais | idem |
| situação cadastral de empresa | cadastro nacional de pessoas jurídicas | idem |
| códigos de municípios | instituto oficial de estatística | tabela de referência |
| feriados nacionais, estaduais e municipais | atos oficiais | necessário para contagem em dias úteis |
| índices de preços para reajuste | instituto que publica o índice | fonte oficial |
| cronogramas e limites fixados pela própria agência | normas da agência | a agência é a fonte |

Cuidados com dados de fontes externas:

- **Histórico.** Muitas consultas públicas mostram apenas a **situação atual**. Para validar uma habilitação na data do fato, é preciso o **histórico** (datas de concessão, suspensão, restabelecimento, cancelamento). Se a consulta pública não traz o histórico, registre como lacuna do tipo "dado inexistente" e peça o histórico por ofício ao órgão responsável ou por acesso a um conjunto de dados abertos.
- **Data da consulta.** Guarde cada versão baixada com a data de obtenção, para que o verificador possa ser reexecutado com os mesmos dados.
- **Automação da obtenção.** Sempre que possível, escreva um procedimento que baixa a lista oficial e a converte para o formato usado pelo verificador.

## 3.4 Dados pedidos ao regulado

Para cada dado que só o regulado detém, confirme a **base legal da obrigação de registro**. Em regulação, ela costuma estar em:

- cláusula do contrato de concessão ou do termo de autorização que obriga a manter registros e a fornecê-los à agência;
- dispositivo da própria norma que cria a obrigação (por exemplo, "a concessionária manterá registro das inspeções recebidas");
- norma geral de prestação de informações da agência.

Se o dado **não é registrado hoje** (por exemplo, a data em que o regulado recebeu um documento), há duas saídas: exigir o registro daqui em diante (e tratar o passado como lacuna) ou adaptar a regra para usar um dado existente, registrando a aproximação como parâmetro.

Peça ao regulado o **universo completo**, sem filtros. É a agência quem aplica o escopo. No caso de origem, a orientação foi enviar todas as unidades, inclusive suspensas e desligadas, porque o escopo era uma lacuna ainda não decidida; se o regulado filtrasse, a decisão futura não poderia ser aplicada sem novo pedido.

## 3.5 Organize em blocos

Agrupe os dados em **blocos**, cada um correspondendo a um tipo de registro com chave própria:

| Bloco típico | Conteúdo | Chave |
|---|---|---|
| universo | unidades, contratos, ativos, usuários sujeitos à obrigação | identificador da unidade |
| eventos | o fato que cumpre a obrigação (inspeção, resposta, obra, medição) | identificador do evento |
| consequências | o fato que decorre do descumprimento (interrupção, compensação, notificação) | identificador da consequência |
| habilitações | terceiros habilitados pelo regulado, com períodos de vigência | documento + data de início |
| referências | tabelas que o regulado mantém e que a regra usa (metas, cronogramas internos) | conforme o caso |

Os blocos se ligam por **referências** (por exemplo, `inspecoes.id_unidade` aponta para `unidades.id_unidade`).

## Lista de verificação da etapa

- [ ] Cada dado aponta para a linha da regra que o usa.
- [ ] Para cada dado: detentor, base legal, granularidade, histórico, chave, dado pessoal.
- [ ] Dados públicos identificados e com fonte oficial definida; histórico disponível ou lacuna registrada.
- [ ] Dados não registrados hoje tratados (exigir daqui em diante ou adaptar a regra).
- [ ] Universo completo pedido, sem filtro de escopo pelo regulado.
- [ ] Blocos definidos, com chaves e referências.
