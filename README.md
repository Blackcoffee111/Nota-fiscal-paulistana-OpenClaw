# Robô de Notas Fiscais (NFS-e São Paulo) para OpenClaw

Este pacote dá ao seu assistente virtual (OpenClaw) a capacidade de **emitir, cancelar e baixar relatórios** de Notas Fiscais de Serviço (NFS-e) direto no sistema da Prefeitura de São Paulo — tudo pelo chat, conversando em português.

Você **não precisa ser programador** para usar. O próprio robô faz a configuração com você, passo a passo.

---

## 📑 Índice

- [Início rápido (instalação)](#-início-rápido-instalação)
- [Configuração manual (avançado)](#️-configuração-manual-para-usuários-avançados)
- [Novidades 2026 — a Reforma Tributária](#-novidades-2026--a-reforma-tributária)
  - [Layout 1 (PCC) e Layout 2 (IBSCBS): qual usar](#qual-layout-usar--em-2026-é-você-quem-escolhe)
  - [Os códigos fiscais do Layout 2 e como achá-los](#-os-códigos-fiscais-do-layout-2-e-como-achá-los)
- [Documentação e fontes oficiais](#-documentação-e-fontes-oficiais)

---

## 🚀 Início rápido (instalação)

A forma mais fácil é deixar o **robô configurar tudo** — ele tem um assistente embutido. Não precisa abrir nenhum arquivo de código.

### 1. Coloque a pasta no lugar certo
Copie todos estes arquivos para a "Central de Habilidades" (Skills) do seu OpenClaw — normalmente em `workspace/skills/` (ex.: crie a pasta `faturamento_sp` lá dentro e ponha tudo nela).

### 2. Chame o robô e deixe ele te guiar
Abra o chat e diga algo como *"Emita uma nota"* ou *"Preciso testar a skill de nota fiscal"*. Na primeira vez, o robô percebe que ainda não está configurado e conduz a instalação:

- **Instala as dependências** automaticamente (bibliotecas Python necessárias).
- **Entrevista você** pelo chat: pede CNPJ, Inscrição Municipal, Código de Serviço e a alíquota de ISS. Se você não souber a alíquota, ele pesquisa e sugere.
- **Prepara o arquivo de senha** (`.env`) e te orienta a preenchê-lo.

### 3. Adicione seu Certificado Digital e a senha
São as duas únicas etapas manuais, por segurança:

- **Certificado:** copie seu arquivo `.p12` (ou `.pfx`) para dentro da pasta do projeto. O robô pergunta o nome do arquivo no chat.
- **Senha:** ela mora num arquivo oculto chamado **`.env`** (começa com ponto). Abra-o num editor de texto e troque o lado direito do `=`:
  ```
  NFSE_CERT_PASSWORD=suasenhaverdadeira
  ```
  > 💡 No Mac, arquivos que começam com ponto ficam ocultos. Aperte `Command + Shift + .` para vê-los.
  >
  > 🔒 Por segurança, o robô **nunca lê** a sua senha — ele assume que você a preencheu e segue para a validação.

### 4. Teste de validação ("Batismo de Fogo")
Com certificado e senha no lugar, o robô faz automaticamente uma **emissão de teste de R$ 150,00** (modo teste, não gera nota real) para confirmar que a assinatura digital e a conexão com a Prefeitura funcionam. Passou no teste, você está pronto para emitir notas reais.

### ⚙️ Configuração manual (para usuários avançados)
Se preferir não usar o assistente, edite o **`config.json`** à mão:
- Troque os campos `"MEUCNPJ"`, `"Minhainscricao"`, `"Meucodigo"` e `"MEUCertificado.p12"` pelos seus dados reais.
- Em `"aliquota_servicos"`, use formato decimal (ex.: `0.02` para 2%).

---

## 🎉 Novidades 2026 — a Reforma Tributária

A versão 2.0 adapta o robô às mudanças tributárias de 2026, em duas frentes — **ambas implementadas e validadas** contra a homologação da Prefeitura (`{"sucesso": true}`).

### Frente 1 — Layout 1 com a nova sistemática PCC (em produção)

Desde **01/01/2026**, a Prefeitura mudou o significado dos campos de PIS, COFINS e CSLL na NFS-e. O robô já emite no formato novo:

| Campo | O que passou a significar |
|---|---|
| `<ValorPIS>` | **Débito próprio** do prestador (sempre preenchido). Lucro Presumido: 0,65% |
| `<ValorCOFINS>` | **Débito próprio** (sempre preenchido). Lucro Presumido: 3% |
| `<ValorCSLL>` | **Soma das retenções** PIS+COFINS+CSLL (4,65%), quando há retenção |
| `<TipoRetencao>` | Anunciado pela Prefeitura, mas o webservice ainda não aceita — mantido desligado por flag |

**Na prática para você:** suas notas saem normalmente; muda só a estrutura interna do XML, que agora permite à Receita cruzar seus débitos próprios com as retenções dos tomadores. Detalhes em [`SP_PCC_2026.md`](SP_PCC_2026.md).

### Frente 2 — Layout 2 (IBSCBS): os novos impostos da Reforma

A Reforma Tributária (EC 132/2023 + LC 214/2025) cria dois impostos que substituirão os atuais:

- **CBS** → substitui PIS + COFINS (federal)
- **IBS** → substitui ISS + ICMS (estadual/municipal)

Os dois funcionam igual e andam juntos (por isso "IBSCBS" — o *IVA Dual* brasileiro). Na NFS-e aparecem no **Layout 2**. O emissor é o script **`emitir_nfse_v2.py`**, separado do `emitir_nfse.py`, e está **validado de ponta a ponta**.

### Qual layout usar — em 2026 é VOCÊ quem escolhe

| Período | Regra |
|---|---|
| **2026** | **Os dois layouts são válidos** (posição oficial da Prefeitura). O Layout 2 destaca IBS/CBS, mas como valores **informativos** — você **não paga nada a mais** (a LC 214 dispensa o recolhimento neste ano). |
| **2027+** | **Layout 2 obrigatório** — a CBS passa a ser cobrada e o PIS/COFINS são extintos. |

> 🤖 **O robô pergunta qual layout usar** ao emitir uma nota em 2026. Se você definir uma preferência fixa, ele a salva no `config.json` (`"layout_preferido": "1"` ou `"2"`) e para de perguntar. A partir de 2027 ele usa o Layout 2 sozinho.

**Vale antecipar o Layout 2 em 2026?** É opcional, mas um bom ensaio sem risco: valida toda a integração antes da obrigatoriedade de 2027, sem custo. A abordagem **híbrida** (emitir real no Layout 1 + testar o Layout 2 em modo teste) é a mais segura.

**Marco crítico: 01/01/2027** — quando o Layout 2 passa a ser obrigatório. Já está pronto para esse dia.

### 🔑 Os códigos fiscais do Layout 2 (e como achá-los)

O Layout 2 exige três códigos que classificam o serviço para o IBS/CBS:

| Código | O que é | Onde fica |
|---|---|---|
| **NBS** | Nomenclatura Brasileira de Serviços (9 díg.) — *que serviço é* | `config.json` → `ibscbs.nbs` |
| **cIndOp** | Indicador de operação (6 díg.) — *onde o imposto é devido* | `ibscbs.c_ind_op` |
| **cClassTrib** | Classificação tributária (6 díg.) — *como tributa / se tem redução* | `ibscbs.cclasstrib` |

**Já configurados e validados para MEDICINA (item 04.01 da LC 116):**
- `nbs = 123012200` (serviços médicos especializados)
- `c_ind_op = 030101` (local da prestação)
- `cclasstrib = 200029` (saúde humana, Anexo III — **com redução de alíquota**)

**Como achar para qualquer serviço:**
1. Abra o **Anexo VIII** (tabela de correlação), já arquivado em [`schemas_oficiais_sp/`](schemas_oficiais_sp/) ou baixe em [gov.br/nfse → documentação técnica → RTC](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc).
2. Abra a aba **"tabela geral"**.
3. Procure pelo **Item da LC 116** do seu serviço (medicina = grupo `04.xx`) ou pela descrição.
4. Leia as colunas **NBS**, **INDOP** (=cIndOp) e **cClassTrib**.
5. No `config.json`, escreva o NBS sem pontos (`1.2301.22.00` → `123012200`).

> ⚠️ **Saúde tem redução de alíquota.** Médicos/clínicas usam `cClassTrib 200029`, **não** `000001` (tributação integral) — usar o código errado paga imposto a mais. Os itens 04.01 (medicina) e 04.03 (clínica/hospital) têm a **mesma tributação**; muda só o NBS.

---

## 📚 Documentação e fontes oficiais

**Guias internos:**
- [`SP_PCC_2026.md`](SP_PCC_2026.md) — detalhes do Layout 1 / sistemática PCC
- [`MIGRATION_RTC_2026.md`](MIGRATION_RTC_2026.md) e [`RTC_2026_README.md`](RTC_2026_README.md) — detalhes do Layout 2 / IBSCBS

**Fontes oficiais arquivadas** (base normativa, snapshot de 06/2026):
- [`fontes_oficiais_prefeitura/`](fontes_oficiais_prefeitura/) — manual do WebService v3.3 e XSDs dos layouts 1 e 2
- [`schemas_oficiais_sp/`](schemas_oficiais_sp/) — XSDs v02 (validação local) + **Anexo VIII** (tabela de correlação de códigos)

**Como o robô se comporta** (definido em `SKILL.md`):
- Pergunta qual layout usar e explica a diferença entre débito próprio e retenção
- Monta o esboço financeiro com as retenções nos campos certos (nunca só no texto)
- Aplica corretamente as regras de PF, PJ e intermediário de serviço
- Valida a validade do certificado e avisa quando faltarem ≤ 30 dias para expirar
- Reconhece os erros comuns da Prefeitura (260, 1001, 1050, 1056/1057, 1206, 630, 268) e sugere a correção

### Estrutura das branches
```
main                  ← tudo: Layout 1 (produção) + Layout 2 (pronto p/ 2027)
rtc-2026-layout-v2    ← histórico do desenvolvimento do Layout 2 (já consolidado na main)
```

---

Para emitir, é só pedir no chat — por exemplo: *"Emita uma nota de R$ 1.500 para a AMIL"*. O robô cuida do cálculo dos impostos, monta a nota, pede sua aprovação e devolve o link do PDF oficial da Prefeitura.
