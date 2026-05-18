# Adequação NFS-e SP — PIS/COFINS/CSLL (PCC) — Vigência 2026

Branch: `sp-pcc-2026`
Origem: comunicado de contador (05/2026) sobre alterações da Prefeitura SP na sistemática de tributos federais nas NFS-e, em adequação à Reforma Tributária.

> ⚠️ **Atenção:** essas mudanças são **distintas** das mudanças federais do IBSCBS (grupo CBS/IBS — branch `rtc-2026-layout-v2`). Aqui tratamos do ajuste **municipal de SP** que muda a **semântica dos campos `<ValorPIS>`, `<ValorCOFINS>` e `<ValorCSLL>`** dentro do Layout v1 atual. **Esta sim já está em vigor** e exige adaptação imediata para emissões de 2026.

---

## 1. O que mudou na NFS-e SP

| Campo XML | Antes (até 2025) | Agora (2026+) |
|---|---|---|
| `<ValorPIS>` | Só preenchido quando havia retenção (valor retido) | **Sempre preenchido** com o débito próprio do prestador |
| `<ValorCOFINS>` | Só preenchido quando havia retenção | **Sempre preenchido** com o débito próprio |
| `<ValorCSLL>` | Só CSLL retido (1% do bruto) | **Soma de PIS + COFINS + CSLL retidos (PCC)** quando houver retenção |
| `<TipoRetencao>` | **Não existia** | **Obrigatório** — código de 0 a 9 indicando o tipo de retenção |
| `<ValorINSS>` | Só na WebService (online ganhou novo nome) | Mantido na WebService; renomeado para "Contribuição Previdenciária – Retida" só no online |

---

## 2. Tabela de TipoRetencao

| Código | Significado |
|:---:|---|
| **0** | PIS/COFINS/CSLL Não Retidos |
| **3** | PIS/COFINS/CSLL Retidos (caso comum AMIL/Unimed/operadoras) |
| 4 | PIS/COFINS Retidos, CSLL Não Retido |
| 5 | PIS Retido, COFINS/CSLL Não Retidos |
| 6 | COFINS Retido, PIS/CSLL Não Retidos |
| 7 | PIS Não Retido, COFINS/CSLL Retidos |
| 8 | PIS/COFINS Não Retidos, CSLL Retido |
| 9 | COFINS Não Retido, PIS/CSLL Retidos |

**No dia-a-dia** (Lucro Presumido + Medicina): use **0** ou **3**.

---

## 3. Alíquotas por regime tributário

| Regime | PIS (débito) | COFINS (débito) | Retenção total PCC |
|---|:---:|:---:|:---:|
| **Lucro Presumido** ← seu caso | 0,65% | 3,00% | 4,65% |
| Lucro Real | 1,65% | 7,60% | 4,65% (retenção é a mesma) |

---

## 4. Exemplo prático: nota de R$ 4.522,50 para AMIL

### XML antigo (até 2025)
```xml
<ValorPIS>29.40</ValorPIS>       <!-- retenção PIS -->
<ValorCOFINS>135.68</ValorCOFINS> <!-- retenção COFINS -->
<ValorCSLL>45.23</ValorCSLL>     <!-- retenção CSLL apenas -->
```

### XML novo (2026+)
```xml
<ValorPIS>29.40</ValorPIS>        <!-- débito próprio (sempre) -->
<ValorCOFINS>135.68</ValorCOFINS> <!-- débito próprio (sempre) -->
<ValorCSLL>210.31</ValorCSLL>     <!-- SOMA: PIS+COFINS+CSLL retidos = 4,65% -->
<TipoRetencao>3</TipoRetencao>    <!-- todos retidos -->
```

### Mesma nota se fosse paciente particular (R$ 500, sem retenção)
```xml
<ValorPIS>3.25</ValorPIS>         <!-- débito próprio 0,65% -->
<ValorCOFINS>15.00</ValorCOFINS>  <!-- débito próprio 3% -->
<TipoRetencao>0</TipoRetencao>    <!-- nada retido -->
<!-- ValorCSLL ausente -->
```

---

## 5. Diferença conceitual: débito próprio vs retenção

- **Débito próprio** = imposto que **você apura mensalmente** na DCTF/EFD-Contribuições e paga via DARF (quando não houver retenção que o quite)
- **Retenção** = imposto que o **cliente desconta** da sua nota e **paga em seu nome** à Receita Federal (vira crédito antecipado seu)

Os dois sempre coexistiram. A novidade é que **a NF-e agora precisa mostrar ambos** — antes mostrava só a retenção.

**Razão da mudança:** permite à Receita Federal cruzar automaticamente:
1. O que aparece como retenção/débito nas NF-e que você emitiu
2. O que está declarado na sua EFD-Contribuições
3. O que o tomador declarou ter retido (DCTF dele)
4. O DARF que você efetivamente pagou

---

## 6. Mudanças aplicadas nesta branch

### 6.1 `config.json` — novo bloco `pcc_2026`
```json
"pcc_2026": {
  "habilitado": true,
  "regime_tributario": "lucro_presumido",
  "debito_proprio": {
    "pis": 0.65,
    "cofins": 3.0
  },
  "retencao_pcc_total": 4.65
}
```
- `habilitado: true` → ativa o novo layout SP 2026
- `habilitado: false` → mantém comportamento legado (compatibilidade total)

### 6.2 `emitir_nfse.py` — refatoração de `construir_xml_lote`
- **Nova função `calcular_tipo_retencao()`** → retorna o código 0/3-9 conforme combinação de retenções
- **Variáveis separadas**: `v_pis_debito` / `v_pis_retido`, idem COFINS — clarifica a semântica
- **Decisão condicional**: quando `pcc_2026.habilitado=true`:
  - `<ValorPIS>` = débito próprio (sempre)
  - `<ValorCOFINS>` = débito próprio (sempre)
  - `<ValorCSLL>` = soma das retenções PCC (quando houver)
  - `<TipoRetencao>` emitido entre `<ValorCSLL>` e `<CodigoServico>`
- **Backward compat**: com `habilitado=false`, o XML sai idêntico ao v1 — emitir_nfse.py original

### 6.3 Validação executada (3 cenários, dry-run com cert real)

| Cenário | Input | Resultado |
|---|---|---|
| 1 - Particular sem retenção | R$ 500,00 PF | ✅ `ValorPIS=3.25` `ValorCOFINS=15.00` `TipoRetencao=0` |
| 2 - AMIL com retenção PCC | R$ 4.522,50 PJ | ✅ `ValorPIS=29.40` `ValorCOFINS=135.68` `ValorCSLL=210.31` `TipoRetencao=3` |
| 3 - Backward compat | habilitado=false | ✅ XML idêntico ao v1 (`ValorCSLL=45.23`, sem TipoRetencao) |

Todos os XMLs foram assinados digitalmente com sucesso.

---

## 7. Pendência: teste real contra homologação SP

Os dry-runs validam **estrutura** mas não **aceitação pela prefeitura**. Especificamente, dois pontos precisam ser confirmados contra o webservice real (`nfews.prefeitura.sp.gov.br/lotenfe.asmx`):

1. **Posição do `<TipoRetencao>`** — está provisoriamente entre `<ValorCSLL>` e `<CodigoServico>`. Se o schema rejeitar (erro 1001), realocar conforme a lista de elementos válidos que a prefeitura retornar.
2. **Nome exato do campo** — usado `<TipoRetencao>`. O email do contador chama de "tipo de retenção" mas o XSD oficial pode usar outro nome (ex: `<TipoRetencaoCSLL>` ou `<TipoRetencaoFontes>`).

**Para rodar o teste real**, restaure seu config real (CNPJ/IM/Inscrição Municipal verdadeiros) e:
```bash
./.venv/bin/python emitir_nfse.py --modo teste --dados nota.json --json-out
```
O endpoint de teste (`TesteEnvioLoteRPS`) **não emite NF-e real** — só valida o XML.

---

## 8. Referências

- Email do contador (05/2026) — alterações na sistemática de tributos federais NFS-e SP
- Lei 10.833/2003 art. 31 — retenções PIS/COFINS/CSLL na fonte
- IN RFB 1.234/2012 — regulamenta retenções PCC para serviços profissionais

---

## 9. Como reverter (se necessário)

```bash
# Voltar para main (Layout v1 legado)
git checkout main

# Manter na branch mas desabilitar o novo comportamento
# editar config.json: "habilitado": false
```
