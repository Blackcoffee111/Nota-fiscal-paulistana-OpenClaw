# ⏳ Branch `rtc-2026-layout-v2` — AGUARDANDO PREFEITURA SP

> **Para o usuário (no futuro, quando ler isto):** Este trabalho foi feito em 18/05/2026 e deixou uma branch pronta esperando uma ação externa da Prefeitura. Este arquivo serve para te lembrar do que ficou pendente, caso você esqueça.

## 📌 Em uma frase

Tem um código já pronto e testado para emitir NF-e no formato novo da Reforma Tributária (com CBS e IBS), mas **só vai poder ser usado quando a Prefeitura de SP publicar o endpoint oficial**. Quando isso acontecer, é só seguir o checklist abaixo.

## 🎯 Como saber se já posso usar

A Prefeitura precisa **publicar uma URL nova** (ou habilitar o IBSCBS na atual) para o webservice de envio de notas. Para checar se já saiu:

1. **Pergunte ao seu contador:** *"O endpoint de Layout 2 da NFS-e SP com IBSCBS já está em produção?"*
2. **Ou peça ao Claude:** *"Cheque se a Prefeitura SP publicou o endpoint v2 do IBSCBS"* — ele vai fazer uma busca web e te dizer
3. **Ou consulte:** https://prefeitura.sp.gov.br/web/fazenda/w/nfs-e_orientacoes (página oficial das orientações da Prefeitura sobre NFS-e e RTC)

**Sinal claro de que está disponível:** a Prefeitura publica uma URL como `https://nfews.prefeitura.sp.gov.br/lotenfe_v2.asmx` ou algo similar, com mention a "Layout 2" e "IBSCBS".

## 📋 O que está pronto na branch

```
rtc-2026-layout-v2:
  ├── emitir_nfse_v2.py        ← scaffold do emissor com grupo <IBSCBS>
  ├── config.json              ← bloco "ibscbs" com alíquotas-teste (CBS 0,9% / IBS 0,1%)
  ├── MIGRATION_RTC_2026.md    ← diff técnico de TODOS os campos novos
  ├── RTC_2026_README.md       ← guia em linguagem simples
  └── NT_04_v2.pdf             ← Nota Técnica oficial federal (15 páginas)
```

## ✅ Checklist para ativar (quando a Prefeitura publicar)

1. **Pedir ao Claude para fazer:**
   ```bash
   cd "~/Library/Application Support/Claude/.../skills/nfe-2"
   git checkout rtc-2026-layout-v2
   ```

2. **Atualizar a URL** em `emitir_nfse_v2.py` (linha onde está `url = "https://nfews.prefeitura.sp.gov.br/lotenfe.asmx"`) para a URL nova divulgada pela Prefeitura

3. **Confirmar com seu contador** os códigos exatos:
   - `CST` (Código de Situação Tributária IBS/CBS)
   - `cClassTrib` (Código de Classificação Tributária)
   - Atualizar no `config.json` dentro do bloco `ibscbs`

4. **Habilitar o layout:**
   ```json
   "ibscbs": {
     "habilitado": true,    ← mudar para true
     ...
   }
   ```

5. **Testar contra homologação:**
   ```bash
   ./.venv/bin/python emitir_nfse_v2.py --modo teste --dados nota.json --json-out
   ```

6. **Se passar:** mergear na `main`:
   ```bash
   git checkout main
   git merge rtc-2026-layout-v2
   ```

7. **Se der erro 1001** sobre `<IBSCBS>` em posição errada, peça ao Claude para ajustar a posição no XML conforme a mensagem da Prefeitura.

## 🚨 Por que NÃO mergear hoje

- Webservice atual (`lotenfe.asmx`) **rejeita o grupo `<IBSCBS>`** — testado em 18/05/2026, erro 1001
- **LC 214/2025 dispensa o recolhimento** de CBS/IBS em 2026 — ano de teste, sem urgência fiscal
- Mergear cedo demais quebraria as emissões normais

## 📅 Cronograma para você se planejar

| Ano | Situação |
|---|---|
| **2026** | Ano de teste — valores informativos, sem recolhimento. **Aguardar Prefeitura SP** |
| **2027** | CBS começa a valer com alíquota cheia, PIS/COFINS extintos. **OBRIGATÓRIO ter Layout v2 ativo** |
| 2028 | CBS pleno |
| 2029-2032 | Transição gradual ISS → IBS (redução de 10% ao ano do ISS) |
| 2033 | IBS pleno, ISS extinto |

> **Marco crítico:** até **01/01/2027** o Layout v2 PRECISA estar funcionando, senão suas emissões vão começar a dar problema com a Receita Federal.

## 🆘 Se eu esquecer e mergeei sem testar?

Sem pânico:
```bash
cd "~/Library/Application Support/Claude/.../skills/nfe-2"
git log --oneline    # achar o commit antes do merge errado
git reset --hard <commit_hash>
```

A branch `rtc-2026-layout-v2` continua intacta, dá pra refazer.

---

**Última validação contra homologação:** 18/05/2026 — Prefeitura retornou erro 1001 ao receber `<IBSCBS>`. Confirma que ainda não está habilitado.
