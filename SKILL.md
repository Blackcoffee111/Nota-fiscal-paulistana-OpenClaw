---
description: Faturamento NFS-e SP (Emissão e Cancelamento de Notas Fiscais em São Paulo)
---

<!-- Discriminação padrão: SERVIÇOS PRESTADOS PELOS PRÓPRIOS SÓCIOS NO EXERCÍCIO DE PROFISSÃO REGULAMENTADA POR LEGISLAÇÃO FEDERAL, ISENTO DA RETENÇÃO DO INSS CONFORME PREVISTO NO ART. 120, INCISO III, § 2º DA IN/RFB Nº 971/2009. -->

# Habilidade de Faturamento NFS-e SP (OpenClaw)

> ## 🗂️ DOIS LAYOUTS COEXISTEM — PERGUNTE AO USUÁRIO qual usar
>
> | Layout | Script | Situação | Status |
> |---|---|---|---|
> | **Layout 1** (só ISS + PCC) | `emitir_nfse.py` | Válido em 2026; **não** destaca IBS/CBS | ✅ Validado |
> | **Layout 2** (com IBSCBS) | `emitir_nfse_v2.py` | Válido em 2026; destaca IBS/CBS (informativos); **obrigatório a partir de 2027** | ✅ Validado |
>
> **Fato oficial (Prefeitura SP):** em **2026 os DOIS layouts são válidos** — o contribuinte escolhe. O destaque de IBS/CBS é **facultativo** em 2026 (a LC 214/2025 dispensa o *recolhimento*; o sistema não bloqueia emissão sem o destaque). A partir de **01/01/2027 o Layout 2 passa a ser obrigatório** e os tributos passam a ser recolhidos. Ambos foram validados contra a homologação SP (`{"sucesso": true}`).
>
> ### 🟢 REGRA DE OURO DO AGENTE: pergunte, não presuma
> Ao receber um pedido de emissão, **PERGUNTE ao usuário em qual layout ele quer emitir** (a menos que ele já tenha dito, ou que exista preferência salva — ver abaixo). Apresente a escolha de forma curta e clara, por exemplo:
> > *"Em qual layout quer emitir esta nota?*
> > *• **Layout 1** — formato tradicional, só ISS. Mais simples. Válido em 2026.*
> > *• **Layout 2** — já com IBS/CBS destacados (Reforma Tributária). Em 2026 os valores são informativos, você não paga nada a mais. Vira obrigatório em 2027 — usar agora é um bom 'ensaio'.*
> > *Qual prefere?"*
>
> Regras de apoio à decisão:
> - **A partir de 2027** (verifique a data atual): use sempre o **Layout 2**, sem perguntar (é obrigatório).
> - Se o usuário **não tiver preferência** ou pedir sua recomendação: sugira a **abordagem híbrida** — emitir a nota real no Layout 1 (simples) e, se ele quiser, rodar um teste em Layout 2 (`--modo teste`) para validar a preparação para 2027.
> - Se o usuário **definir uma preferência fixa** ("sempre use o Layout 2", "daqui pra frente Layout 1"), **registre no `config.json`** o campo `"layout_preferido": "1"` ou `"2"` e **deixe de perguntar**, usando essa escolha. Se o campo existir, respeite-o.
> - Para o **Layout 2**, antes da PRIMEIRA emissão real, confirme o enquadramento fiscal (item LC 116 → NBS/cClassTrib/cIndOp) — ver seção "🆕 Layout 2".
>
> Detalhes do Layout 2: ver seção "🆕 Layout 2 (IBSCBS)" mais abaixo e `MIGRATION_RTC_2026.md`.

Esta documentação define o comportamento e as arquiteturas da Skill de faturamento para emitir e cancelar Notas Fiscais de Serviços Eletrônica (NFS-e) da Prefeitura de São Paulo.

> **Importante:** Todos os arquivos descritos abaixo devem estar contidos na mesma pasta desta Skill (ex: `workspace/skills/nfse-sp/`).

## 📁 Arquivos do Ecossistema
1. `emitir_nfse.py` - **Emissor de produção (Layout 1 + PCC 2026)** — gera o XML SOAP, assina e envia.
2. `cancelar_nfse.py` - Script de cancelamento de notas (criptografa o cancelamento).
3. `config.json` - Dados da empresa, retenções, alíquotas, bloco `pcc_2026` (Layout 1) e bloco `ibscbs` (Layout 2).
4. `tomadores.json` - Tabela de dados de clientes recorrentes (sua agenda).
5. `contador_rps.txt` - Arquivo de controle rigoroso para a sequência do talão.
6. `Certificados.p12` - Chave criptográfica municipal (JAMAIS EXPOR).
7. `.env` - Arquivo oculto onde você lerá a variável `NFSE_CERT_PASSWORD=senha`.
8. `baixar_notas.py` - Script paginado de extração de relatórios e balanços contábeis da clínica.
9. `SP_PCC_2026.md` - Documentação das mudanças PIS/COFINS/CSLL do Layout 1 (em vigor desde 05/2026).
10. `emitir_nfse_v2.py` - **Emissor do Layout 2 (IBSCBS / Reforma Tributária)** — pronto para 2027. Tem `--selftest` (valida assinatura) e validação local contra XSD.
11. `MIGRATION_RTC_2026.md` / `RTC_2026_README.md` - Documentação técnica e guia do Layout 2.
12. `schemas_oficiais_sp/` - XSDs oficiais v02 (validação local) + **Anexo VIII** (tabela de correlação de códigos NBS/cIndOp/cClassTrib).
13. `fontes_oficiais_prefeitura/` - Manual do WebService v3.3 e XSDs oficiais arquivados.

---

## 🗓️ Contexto Tributário 2026 (LEIA SEMPRE ANTES DE EMITIR)

A partir de 2026, há **duas frentes de mudança** correndo em paralelo. Você precisa conhecê-las para responder corretamente ao usuário e calcular valores certos.

### Frente 1 — PCC 2026 (Prefeitura SP) — ✅ **EM VIGOR E ATIVADA**

Ajuste municipal de SP na semântica dos campos de tributos federais na NFS-e, em vigor desde **01/01/2026**. Está validada contra a homologação SP (resposta da prefeitura: `"sucesso": true` em 18/05/2026).

**O que mudou** (já implementado no `emitir_nfse.py`):

| Campo XML | Semântica antiga (até 2025) | Semântica nova (2026+) |
|---|---|---|
| `<ValorPIS>` | Valor RETIDO (só preenchia se houvesse retenção) | **DÉBITO PRÓPRIO** — sempre preenchido (Lucro Presumido: 0,65% × valor) |
| `<ValorCOFINS>` | Valor RETIDO | **DÉBITO PRÓPRIO** — sempre preenchido (Lucro Presumido: 3% × valor) |
| `<ValorCSLL>` | Valor RETIDO de CSLL apenas (1%) | **SOMA das retenções PCC** (PIS+COFINS+CSLL = 4,65%) quando houver retenção |
| `<ValorIR>` | IRRF retido (1,5%) | Inalterado |
| `<TipoRetencao>` | Não existia | **Anunciado mas ainda NÃO aceito pelo webservice** (mantido desabilitado via flag `pcc_2026.emitir_tipo_retencao=false`) |

**Diferença conceitual que você deve saber explicar ao usuário:**
- **Débito próprio** = imposto que o prestador apura mensalmente na DCTF/EFD-Contribuições e paga via DARF
- **Retenção** = imposto descontado pelo tomador (cliente PJ) e pago em nome do prestador — vira crédito antecipado
- A retenção da AMIL/operadoras (PCC 4,65%) **quita** o PIS/COFINS próprios do prestador automaticamente. CSLL trimestral pode sobrar diferença

**Implicação no Esboço Financeiro (passo 3 da emissão):**
- SEMPRE mostrar PIS e COFINS de débito próprio (mesmo sem retenção)
- Quando houver retenção do tomador PJ (≥ R$ 666,67), mostrar a linha "Retenção PCC 4,65%: R$ X" consolidada
- Líquido = valor bruto − retenção PCC (se houver) − IRRF (se aplicável)

**Referências completas:** `SP_PCC_2026.md` na pasta da skill.

### Frente 2 — RTC / IBSCBS (Reforma Federal) — ✅ **IMPLEMENTADO E VALIDADO**

Reforma Tributária do Consumo (EC 132/2023 + LC 214/2025). Introduz CBS (substitui PIS/COFINS) e IBS (substitui ISS/ICMS), com grupo XML `<IBSCBS>`. O emissor é `emitir_nfse_v2.py`.

**Status (07/06/2026):**
- ✅ `emitir_nfse_v2.py` implementa o RPS v02 completo, validado contra o XSD oficial e contra a homologação SP (`{"sucesso": true}`)
- ✅ Endpoint: o mesmo `nfews.prefeitura.sp.gov.br/lotenfe.asmx`, com `VersaoSchema=2`
- **LC 214/2025 dispensa o recolhimento** de CBS/IBS em 2026 — por isso o **Layout 1 continua o padrão de produção em 2026**
- Layout 2 fica pronto para acionar a partir de 2027

**Cronograma futuro:**
- 2026: ano-teste, valores informativos, sem recolhimento → **use Layout 1**
- 2027: CBS entra valendo, PIS/COFINS extintos → **migrar para Layout 2**
- 2029-2032: transição gradual ISS → IBS
- 2033: IBS pleno

**Comportamento esperado do agente:** em 2026, continuar emitindo no Layout 1 (`emitir_nfse.py`). Só usar `emitir_nfse_v2.py` se o usuário pedir explicitamente o Layout 2/IBSCBS, ou a partir de 2027. Ver a seção "🆕 Layout 2 (IBSCBS)" mais abaixo para o passo a passo.

**Referências completas:** `MIGRATION_RTC_2026.md` e `RTC_2026_README.md`.

### Resumo prático para o agente

| Situação | Ação |
|---|---|
| Usuário pede emissão normal (2026) | Use `emitir_nfse.py` (Layout 1 + PCC 2026 ativo) |
| Usuário pede emissão no Layout 2 / IBSCBS | Use `emitir_nfse_v2.py` — ver seção "🆕 Layout 2" abaixo |
| Usuário pergunta sobre IBSCBS / Reforma Tributária | Explique: implementado e pronto; em 2026 sem recolhimento (LC 214); vira obrigatório em 2027 |
| Usuário pergunta por que ValorPIS aparece sem retenção | Explique: é o débito próprio, em vigor desde 2026 |
| Usuário pergunta por que ValorCSLL é maior que antes | Explique: agora é a soma PCC (4,65%), não só CSLL (1%) |
| Webservice retorna erro 1001 mencionando `<TipoRetencao>` | Confirme que a flag `emitir_tipo_retencao` está `false` no config |
| Usuário não sabe o código NBS/cIndOp/cClassTrib | Consulte o Anexo VIII — ver "🆕 Layout 2 → Como achar os códigos" |
| Vai montar o payload de uma emissão | **SEMPRE** `calcular_retencoes: true`; **nunca** escreva retenção na `discriminacao` — o script preenche os campos `<ValorPIS/COFINS/CSLL/IR>` |
| Nota para **Pessoa Física** (CPF) | **Sem retenção** — só débito próprio PIS/COFINS. O script zera IRRF/PCC automaticamente; o esboço não deve mostrar linha de retenção |
| Nota para PJ que não retém (ex: Simples) | Adicione `"tomador_retem": false` no JSON |

---

## 🆕 Layout 2 (IBSCBS / Reforma Tributária) — manual operacional do agente

> Use esta seção **apenas** quando o usuário pedir emissão no Layout 2 / IBSCBS, ou a partir de 2027. Em 2026, o padrão é o Layout 1 (`emitir_nfse.py`).

### Como emitir no Layout 2
O script é `emitir_nfse_v2.py` (mesmas flags do v1, + `--selftest` e `--no-validate`):
```bash
python emitir_nfse_v2.py --selftest                                  # valida a assinatura (offline, sem cert)
python emitir_nfse_v2.py --modo teste --dados nota.json --dry-run    # monta + valida XML vs XSD (offline)
python emitir_nfse_v2.py --modo teste --dados nota.json --json-out   # teste real (homologação, não emite)
python emitir_nfse_v2.py --modo producao --dados nota.json --json-out # emissão REAL
```
O script **valida o XML localmente contra o XSD oficial** (`schemas_oficiais_sp/xsd_completo/`) antes de enviar — se acusar erro de estrutura, corrija antes de gastar requisição.

### Diferenças do payload JSON no Layout 2
O RPS v2 NÃO tem `valor_servicos`. Use estes campos na nota:
- `valor_final_cobrado` (valor total da nota, com tributos) — substitui `valor_servicos`
- `valor_pis`, `valor_cofins`, `valor_inss`, `valor_ir`, `valor_csll` (valores já calculados)
- `valor_ipi` (0 para serviços), `exigibilidade_suspensa` (0), `pagamento_parcelado_antecipado` (0)
- Os códigos IBSCBS (`nbs`, `c_ind_op`, `cclasstrib`) vêm do `config.json`, bloco `ibscbs`

### 🔎 Como achar os códigos NBS / cIndOp / cClassTrib (FAÇA ISSO quando faltar)
São 3 códigos que classificam o serviço para o IBS/CBS. **Você (agente) deve buscá-los assim:**

1. **Abra a tabela oficial** já arquivada: `schemas_oficiais_sp/AnexoVIII-Correlacao-Item-NBS-IndOp-cClassTrib_*.xlsx`
   (se não existir, baixe de [gov.br/nfse → doc. técnica → RTC](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc), arquivo `anexoviii-correlacao...xlsx`)
2. **Leia a aba `"tabela geral"`** com openpyxl. Colunas: `Item LC 116 | Descrição | NBS | INDOP | cClassTrib`
3. **Filtre pelo Item da LC 116** do serviço do usuário (medicina = grupo `04.xx`) ou pela descrição
4. **Extraia** NBS, INDOP (=cIndOp) e cClassTrib da linha
5. **Formate o NBS** removendo pontos: `1.2301.22.00` → `123012200` (9 dígitos)
6. **Grave no `config.json`**, bloco `ibscbs`: `nbs`, `c_ind_op`, `cclasstrib`
7. **Sempre confirme com o usuário/contador** o enquadramento (item correto) — o NBS muda por especialidade

Exemplo de leitura da tabela (rode no terminal):
```python
import openpyxl
wb = openpyxl.load_workbook('schemas_oficiais_sp/AnexoVIII-Correlacao-Item-NBS-IndOp-cClassTrib_v1.01.00.xlsx', data_only=True)
ws = wb['tabela geral']
for r in ws.iter_rows(values_only=True):
    if r[0] and str(r[0]).startswith('04.'):   # serviços de saúde
        print(r[0], '| NBS', r[2], '| cIndOp', r[6], '| cClassTrib', r[8])
```

### Valores já validados (MEDICINA — item 04.01, no config por padrão)
| Campo | Valor | Significado |
|---|---|---|
| `nbs` | `123012200` | Serviços médicos especializados (NBS 1.2301.22.00) |
| `c_ind_op` | `030101` | Local de incidência: local da prestação |
| `cclasstrib` | `200029` | Saúde humana (Anexo III) — **com redução de alíquota** |

⚠️ **Saúde NÃO é tributação integral.** Use `cClassTrib 200029` (redução ~60%), nunca `000001`. Itens 04.01 (medicina) e 04.03 (clínica/hospital) têm a **mesma tributação** — só muda o NBS. Veterinária (05.01) é diferente (`200052`, redução 30%); planos de saúde (04.22) usam regime próprio (`820001`).

### Catálogo de erros do Layout 2 (já mapeados nos testes)
| Código | Causa | Correção |
|---|---|---|
| **630** | "Código indicador da operação inexistente" | `c_ind_op` inválido — pegue o correto no Anexo VIII |
| **268** | "Código NBS informado inválido" | `nbs` inválido — pegue no Anexo VIII e remova os pontos |
| **640** | "ValorInicialCobrado não disponível" | Use `valor_final_cobrado` no JSON (o script já faz isso) |
| **648** (alerta) | "PagamentoParceladoAntecipado desconsiderado" | Apenas alerta, não bloqueia |

---

## ✨ 0. O Wizard de Instalação (Health Check Automático)
Sempre que o usuário solicitar qualquer ação financeira pela primeira vez (ou se você notar que há algo faltando), você **deve** fazer um check-up silencioso lendo o arquivo `config.json`.
Se os campos contiverem palavras-chave genéricas como `"MEUCNPJ"`, `"Minhainscricao"`, `"MEUCertificado.p12"` ou o valor **`0.0`** no campo `aliquota_servicos`, significa que o usuário acabou de instalar sua Skill e é um humano leigo. 

Neste caso, pause a tarefa dele e inicie um **Wizard de Instalação Interativo e Amigável** no chat:
0. **Check de Dependências (Obrigatório):** Antes de tudo, rode no terminal `pip install -r requirements.txt` para garantir que as bibliotecas `requests`, `lxml`, `signxml`, `cryptography` e `python-dotenv` estejam presentes. **Não tente emitir sem garantir o sucesso desta instalação.**
1. Diga que percebeu que é a primeira vez dele e peça, um por vez, os dados faltantes: O CNPJ, a Inscrição Municipal, o Código de Serviço e a **Alíquota de Serviços (ISS)**.

> [!IMPORTANT]
> **BLOQUEIO DE SEGURANÇA NA ALÍQUOTA:**
> Você deve obrigatoriamente aguardar a resposta do usuário sobre a alíquota. 
> * **Proibido Avançar:** Não use o valor padrão de 2% (0.02) por conta própria caso o arquivo contenha 0.0 ou 0.
> * **Ação Necessária:** Pergunte: *"Qual a alíquota de imposto municipal (ISS) para o seu código de serviço? Posso ajudá-lo a descobrir se não souber."*
> * **Ajuda Ativa:** Se ele não souber, use sua habilidade de pesquisa (Google) cruzando o Código de Serviço dele com as alíquotas de São Paulo e sugira: *"Encontrei que para o serviço X a alíquota em SP costuma ser Y%. Confirma este valor?"*
> * **Condição de Saída:** Você só pode seguir para o faturamento ou para o próximo passo se o usuário digitar um número ou disser "Sim/Confirmo" para sua sugestão.
3. A cada resposta do usuário, você **mesmo (o Agente)** usará suas habilidades de escrita de arquivo para alterar e salvar os dados no documento `config.json` por ele.
4. **Ato Autônomo com o .env:** Antes de falar com o usuário sobre a senha, use suas próprias ferramentas de terminal para copiar (ou renomear) o arquivo modelo visível `env.example` para `.env` (oculto com ponto) na pasta. Deixe este arquivo preparado para receber a senha.
5. **Privacidade Rigorosa do .env:** Por razões de segurança e proteção de senhas bancárias, você (o Agente) **JAMAIS** deve ler o conteúdo do arquivo `.env` para conferir se o usuário já preencheu a senha. 
   - Sempre parta do princípio de que a senha foi inserida conforme orientado. 
   - Comunique ao usuário explicitamente: *"Por sua segurança, eu não tenho permissão para ler seu arquivo .env e ver sua senha. Vou acreditar que você já a inseriu e seguiremos com o teste!"*
6. Quando tudo isso acabar e o `.env` oculto estiver pronto, informe-o sobre a etapa final de segurança (A Senha e o Certificado) orientando-o exatamente desta forma:
> *"Pronto, preenchi os dados da sua empresa e preparei o terreno! Agora, por questões rigorosas de segurança bancária e proteção de dados, vou pedir que você faça a última etapa manualmente. Abra a pasta técnica deste projeto no seu computador (geralmente em `~/.openclaw/workspace/skills/`). Arraste para lá o seu arquivo de certificado real (ex: `Certificado.p12`). Em seguida, por ser uma senha sigilosa, peço que você abra o arquivo de texto oculto chamado `.env` (se vc usa Mac, aperte `Command + Shift + .` para ver os arquivos ocultos). Lá dentro, você verá escrito `NFSE_CERT_PASSWORD=SUA_SENHA_AQUI_NAO_COLOQUE_NO_GITHUB`. Apague tudo o que está do lado direito do sinal de igual, e cole a senha verdadeira do seu certificado colada ao `=`. Feche e salve. Me avise no chat quando terminar!"*
7. Após o usuário confirmar que fez as cópias, atualize no `config.json` o nome exato do arquivo `.p12` que ele disse ter copiado para a pasta, e agora, você deve prosseguir para o **Passo Final de Validação Técnica**.

8. **"Batismo de Fogo" (Teste de Emissão Obrigatório):** Antes de considerar a instalação concluída, você **DEVE** realizar um faturamento de teste para validar a assinatura digital e a conexão com a prefeitura.
   - **Ação Autônoma:** Gere silenciosamente o arquivo `/tmp/test_instalacao.json` com os seguintes dados:
     * `valor_servicos`: 150.00
     * `indicador_tomador`: 2 (CNPJ)
     * `documento_tomador`: "00000000000191"
     * `razao_social_tomador`: "CLIENTE TESTE - OPENCLAW"
     * `iss_retido`: "N"
     * `discriminacao`: "Teste técnico de integração e assinatura digital - OpenClaw"
   - **Execução:** Rode obrigatoriamente: `python3 emitir_nfse.py --modo teste --dados /tmp/test_instalacao.json --json-out`
   - **Conclusão:** 
     * Se o retorno for `Sucesso: True`, parabenize o usuário: *"Parabéns! Sua instalação foi validada com sucesso em modo teste. Agora você já pode emitir notas reais!"*
     * Se der erro, analise o código de erro retornado pela Prefeitura e ajude o usuário a corrigir os dados (ex: se o erro for 1056/1057, cheque a Inscrição Municipal ou a Senha). 
     * **NUNCA** incremente o `contador_rps.txt` após um teste, seja bem ou mal sucedido

---

## 🚀 1. O Fluxo de Coleta e Emissão no Chat

> ### 🟢 PASSO ZERO — QUAL LAYOUT? (decida ANTES de montar a nota)
> Antes de qualquer cálculo, defina o layout nesta ordem de prioridade:
> 1. **Data ≥ 01/01/2027?** → use **Layout 2** (`emitir_nfse_v2.py`), obrigatório. Não pergunte.
> 2. **Existe `"layout_preferido"` no `config.json`?** → respeite ("1" = Layout 1 / "2" = Layout 2). Não pergunte.
> 3. **O usuário já disse o layout no pedido?** → use o que ele disse.
> 4. **Caso contrário (2026, sem preferência):** **PERGUNTE ao usuário** qual layout quer, explicando rápido (ver script de pergunta na "Regra de ouro" no topo do arquivo). Os dois são válidos em 2026; o Layout 2 destaca IBS/CBS (informativos, sem recolhimento).
>
> Depois de decidido: **Layout 1 → `emitir_nfse.py`** (este fluxo, passo 5). **Layout 2 → `emitir_nfse_v2.py`** (ver seção "🆕 Layout 2" para o payload e os códigos). O restante das 6 etapas (triagem, esboço, oitiva, entrega) vale para os dois.

Siga as 6 etapas abaixo sempre que o usuário solicitar emissão:

**1. Recepção de Pedido:** O usuário pedirá a nota (Valor e Tomador). Ex: "Nota de 1500 para a AMIL". **Resolva o PASSO ZERO acima (qual layout) antes de prosseguir.**
**2. Triagem Local (`tomadores.json`):** Leia o arquivo `tomadores.json` em background. Se o Tomador já estiver cadastrado, puxe o CNPJ, endereço e e-mail de lá. Se for inédito, peça ao usuário os dados faltantes.
**3. Simulação Financeira (Draft):** Calcule os impostos internamente cruzando com as regras do `config.json`. Responda ao usuário com um "Esboço" detalhado seguindo a estrutura **PCC 2026** abaixo:

> **Modelo do Esboço Financeiro (2026+):**
>
> | Item | Alíquota | Valor (R$) |
> |---|---:|---:|
> | **Valor bruto dos serviços** | — | X,XX |
> | **Débitos próprios (informativos na NF-e):** | | |
> | ↳ PIS (Lucro Presumido) | 0,65% | informativo |
> | ↳ COFINS (Lucro Presumido) | 3,00% | informativo |
> | **Retenções federais (descontam do valor recebido):** | | |
> | ↳ Retenção PCC consolidada (quando tomador PJ ≥ R$666,67) | 4,65% | −X,XX |
> | ↳ IRRF (quando > R$10) | 1,50% | −X,XX |
> | **Valor líquido a receber** | | X,XX |
> | ISS (destacado, não retido pelo tomador no padrão) | 2% | X,XX |
>
> **Explicação amigável para o usuário:**
> - PIS e COFINS são *débitos próprios* (você apura/paga mensalmente) — aparecem na NF-e desde 2026 mesmo sem retenção
> - Quando o tomador é PJ ≥ R$666,67, ele retém PCC (PIS+COFINS+CSLL = 4,65%) na fonte e paga em seu nome
> - A retenção PCC **quita automaticamente** seu PIS/COFINS próprios do mês; CSLL pode sobrar diferença trimestral
>
> ⚠️ **A tabela acima é para tomador PJ.** Se o tomador for **Pessoa Física** (ou sem identificação / exterior), **REMOVA as linhas de retenção** do esboço — PF **não retém** nada na fonte. O esboço de PF mostra só: valor bruto, débitos próprios PIS/COFINS (informativos), ISS e o líquido (= bruto, pois nada é retido). O script faz isso sozinho, mas o seu esboço deve refletir corretamente.

> ⚠️ **ATENÇÃO - REGRA CRÍTICA DE CARACTERES E QUEBRAS DE LINHA (ERRO 1057):**
> O sistema de assinatura XML da Prefeitura de SP quebra e retorna o Erro 1057 se o payload JSON contiver acentuações, caracteres especiais (ç, ~, ^, ´) ou quebras de linha literais (`\n`) nos campos descritivos e razões sociais. Antes de enviar para o payload:
> - Remova **TODOS** os acentos e "ç" da Razão Social do Tomador e da Discriminação (ex: "SAÚDE" -> "SAUDE", "SERVIÇOS" -> "SERVICOS").
> - Remova quebras de linha (`\n`) da Discriminação, juntando todo o texto em um único parágrafo contínuo.
**4. Oitiva Humana:** Pergunte se o usuário "Aprova o Faturamento".
**5. Emissão e RPS:** 
   * Se aprovado, leia `contador_rps.txt` para pegar o próximo número sequencial X.
   * Gere o arquivo `/tmp/dados_rps_X.json` autônomamente (no Layout 2, use o payload da seção "🆕 Layout 2", com `valor_final_cobrado` em vez de `valor_servicos`).
   * Execute o script **conforme o layout decidido no PASSO ZERO**:
     - **Layout 1:** `python emitir_nfse.py --modo producao --dados /tmp/dados_rps_X.json --json-out`
     - **Layout 2:** `python emitir_nfse_v2.py --modo producao --dados /tmp/dados_rps_X.json --json-out`
   * Imediatamente incremente `contador_rps.txt` (+1).
   * **Boas práticas:** Após o passo acima finalizar, você (o Agente) deve **excluir** o arquivo temporário `/tmp/dados_rps_X.json` para manter o sistema limpo.
**6. Entrega do PDF Final e Envio por E-mail:** Leia a saída JSON do Python. Extraia e devolva ao humano no chat:
   * O sucesso da operação e o Número Final da NF-e gerada.
   * A **URL Oficial de Impressão (PDF)** da prefeitura.
   * **Ação Autônoma Obrigatória:** Como a prefeitura bloqueia o envio público, invoque a sua **Skill GOG (Gestão de E-mails)** e redija um e-mail formatado enviando este link do PDF para o seu próprio e-mail.
   * *Bônus: Se for cliente inédito aprovado, reescreva e salve os novos dados em `tomadores.json`.*

## �️ 2. O Fluxo de Cancelamento de NF-e
Se o usuário pedir explícitamente "Cancele a nota numero N", siga 3 etapas:
1. Revise e peça confirmação: "Deseja mesmo revogar definitivamente a Nota SP Nº N?".
2. Se Sim, invoque via terminal: `python cancelar_nfse.py [N] --json-out`
3. Leia o stdout JSON e informe ao usuário se ela foi cancelada com sucesso no ambiente contábil de São Paulo.

## 📊 3. Fluxo de Relatórios Contábeis (Extrato de Notas)
A qualquer momento o usuário pode solicitar um relatório, balanço total ou extração de faturamentos (Ex: "Feche a contabilidade do mês passado").
Use o script `baixar_notas.py` que consulta a Prefeitura e produz um extrato autônomo. Regras de uso:
1. **Para busca retroativa em dias:** `python baixar_notas.py --dias X` (Padrão 30 dias se o usuário não disser outra coisa).
2. **Para busca em meses/períodos exatos:** `python baixar_notas.py --inicio YYYY-MM-DD --fim YYYY-MM-DD` (O script já tem um loop autônomo que fatiará janelas grandes de >30 dias sem quebrar a API, fique tranquilo).
3. **Resumo Visual:** Leia o console stdout dessa requisição (que contém `Valor Faturado (Bruto Ativo)` e `Notas Ativas`) para dar no chat o seu overview financeiro humano sobre o fechamento pedido.
4. **Exportação Físisca:** A prefeitura exportará tudo formatado em um novo arquivo JSON. Se a oitiva humana do usuário quiser esse relatório em mãos ("Mande essas notas pro contador", ou "Mande pro meu email"), use a sua Skill Nativa GOG e anexe/envie o resultado do arquivo gerado (`nfse_contabilidade.json`) para os e-mails informados.

## 📄 3. Geração do Payload JSON Único para Emissão
Para o Passo 5 acima, gere um `/tmp/dados_rps_XXX.json` unicamente para o atendimento.

> [!IMPORTANT]
> **RETENÇÕES VÃO NOS CAMPOS PRÓPRIOS — NUNCA apenas no texto da discriminação.**
> As retenções (PIS, COFINS, CSLL, IRRF) são gravadas em campos XML específicos
> (`<ValorPIS>`, `<ValorCOFINS>`, `<ValorCSLL>`, `<ValorIR>`), e o **script preenche
> esses campos automaticamente**. Você (agente) NÃO calcula nem escreve valores de
> retenção na mão.
>
> **Regras obrigatórias ao montar o JSON:**
> 1. **SEMPRE inclua `"calcular_retencoes": true`** (Layout 1). Sem isso, os campos de
>    retenção saem em branco — exatamente o erro a evitar. O script lê as alíquotas do
>    `config.json` e preenche `<ValorPIS/COFINS/CSLL/IR>` sozinho.
> 2. **NÃO** escreva valores de imposto/retenção dentro de `discriminacao`. A discriminação
>    é só o texto descritivo do serviço (+ a `mensagem_padrao`, que o script anexa). Os
>    números das retenções pertencem aos campos próprios, não ao corpo do texto.
> 3. **PESSOA FÍSICA NÃO TEM RETENÇÃO.** Retenção na fonte (IRRF/PIS/COFINS/CSLL) só
>    existe quando o **tomador é PJ** (`indicador_tomador: 2`). Para PF (`1`), sem
>    identificação (`3`) ou exterior (`4`), o script **zera as retenções automaticamente**
>    e mantém apenas o **débito próprio** de PIS/COFINS (que independe do tomador). Reflita
>    isso no esboço financeiro: nota para PF não mostra linha de retenção.
>    - *Override raro:* PJ que comprovadamente não retém (ex.: optante do Simples) →
>      adicione `"tomador_retem": false` no JSON.
> 4. **Confirmação visual:** após gerar o JSON, confira que ele tem `calcular_retencoes: true`
>    (PJ) e que nenhum valor de imposto foi parar na `discriminacao`.

> [!IMPORTANT]
> **SANITIZAÇÃO OBRIGATÓRIA ANTES DE MONTAR O JSON (Erro "assinatura difere do calculado"):**
> A Prefeitura de São Paulo valida a assinatura digital comparando o XML recebido com um digest calculado internamente. Acentos e quebras de linha nos campos de texto fazem essa comparação falhar, gerando o erro de assinatura. **Antes de escrever qualquer campo de texto no JSON**, aplique obrigatoriamente as duas regras abaixo:
>
> 1. **Remover acentos e caracteres especiais:** Converta todos os caracteres acentuados para sua versão sem acento nos campos `razao_social_tomador`, `discriminacao`, e em todos os campos de endereço (`logradouro`, `complemento`, `bairro`).
>    - Exemplos: `á→a`, `é→e`, `í→i`, `ó→o`, `ú→u`, `â→a`, `ê→e`, `ô→o`, `ã→a`, `õ→o`, `ç→c`, `Á→A`, `É→E`, `Í→I`, `Ó→O`, `Ú→U`, `Â→A`, `Ê→E`, `Ô→O`, `Ã→A`, `Õ→O`, `Ç→C`.
>
> 2. **Remover quebras de linha:** No campo `discriminacao`, substitua qualquer `\n`, `\r` ou `\r\n` por um espaço simples (` `). Textos com múltiplas linhas devem virar uma única linha contínua.

Modelo:
```json
{
  "numero_rps": <Lido_do_contador_rps.txt>,
  "data_emissao": "AAAA-MM-DD",
  "status_rps": "N",
  "iss_retido": "N",
  "calcular_retencoes": true, // SEMPRE true — o script preenche os campos de retenção. NÃO escreva retenção na discriminacao.
  "valor_servicos": 150.00,
  "indicador_tomador": 2, // 2=CNPJ (PJ, retém na fonte) | 1=CPF (PF, NÃO retém) | 3=Sem ID (não retém) | 4=NIF/exterior (não retém)
  "documento_tomador": "<Apenas_Numeros>",
  // "tomador_retem": false,  // (opcional) só p/ PJ que não retém, ex. Simples Nacional
  "razao_social_tomador": "<Nome_Empresa>",
  "email_tomador": "<Email_Cliente>",
  "endereco_tomador": {
      "logradouro": "RUA X", "numero": "123", "bairro": "VILA Y", "cidade": "3550308", "uf": "SP", "cep": "00000000"
  },
  "discriminacao": "<Suas_Instrucoes_Extras>"
}
```

## 🟢 4. Tratamento do Standard Output
As requisições sempre retornarão um JSON formatado pelo script.
Exemplo de Resposta do Emitir:
```json
{
  "sucesso": true,
  "notas_geradas": [{"numero": "8952", "url_pdf": "https://..."}]
}
```
Exemplo de Resposta do Cancelar:
```json
{
  "sucesso": true,
  "mensagem": "NF-e 642 cancelada com sucesso!"
}
```
Use o parsing inteligente desses JSONs para formular suas respostas humanas ricas e completas no Chat do OpenClaw. Nunca despeje JSON puro para o usuário a menos que solicitado.

## 🚨 5. Códigos de Erro Conhecidos da Prefeitura SP

Quando a prefeitura retorna `"sucesso": false`, traduza para o usuário em linguagem simples e proponha correção. Catálogo de erros mapeados nesta skill:

| Código | Causa provável | Ação sugerida |
|:---:|---|---|
| **260** | CEP do tomador inválido | Validar contra CEPs oficiais SP. Ex: `01310100` (Av. Paulista) |
| **1001** | XML não compatível com Schema | Verifique se algum campo recém-adicionado (ex: `<TipoRetencao>`) foi rejeitado. A mensagem da prefeitura lista os elementos válidos esperados |
| **1050** | Certificado inválido | Verificar validade do `.p12` com `openssl pkcs12 -in Certificados.p12 -nodes` ou inspecionar `cert.not_valid_after_utc` via Python. Renovar com a AC se expirado |
| **1056 / 1057** | Inscrição municipal ou assinatura RPS incorreta | Confirmar IM no portal Nota Paulistana; verificar caracteres especiais na discriminação |
| **1206** | Intermediário em formato inválido | Verificar bloco `intermediario` no JSON da nota |

### 🛡️ Validação preventiva do certificado
**Antes** de qualquer emissão (modo `teste` ou `producao`), você **deve** validar a data de expiração do certificado se não fez isso recentemente. Use:
```bash
./.venv/bin/python -c "from cryptography.hazmat.primitives.serialization import pkcs12; from dotenv import load_dotenv; import os; load_dotenv(); open('Certificados.p12','rb').read() and (lambda p,s: print(pkcs12.load_key_and_certificates(p, s.encode())[1].not_valid_after_utc))(open('Certificados.p12','rb').read(), os.environ['NFSE_CERT_PASSWORD'])"
```
Se faltarem **menos de 30 dias**, avise o usuário proativamente para renovar.
