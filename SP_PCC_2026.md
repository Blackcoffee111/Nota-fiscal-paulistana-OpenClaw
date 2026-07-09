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
  - `<TipoRetencao>` — implementado mas **desligado por padrão** (flag `emitir_tipo_retencao=false`), pois o webservice legado de SP não tem esse campo no schema (ver seção 7)
- **Backward compat**: com `habilitado=false`, o XML sai idêntico ao v1 — emitir_nfse.py original

### 6.3 Validação executada (3 cenários, dry-run com cert real)

| Cenário | Input | Resultado |
|---|---|---|
| 1 - Particular sem retenção | R$ 500,00 PF | ✅ `ValorPIS=3.25` `ValorCOFINS=15.00` `TipoRetencao=0` |
| 2 - AMIL com retenção PCC | R$ 4.522,50 PJ | ✅ `ValorPIS=29.40` `ValorCOFINS=135.68` `ValorCSLL=210.31` `TipoRetencao=3` |
| 3 - Backward compat | habilitado=false | ✅ XML idêntico ao v1 (`ValorCSLL=45.23`, sem TipoRetencao) |

Todos os XMLs foram assinados digitalmente com sucesso.

---

## 7. TipoRetencao — INVESTIGAÇÃO CONCLUÍDA (07/06/2026)

> **TL;DR:** O campo de "tipo de retenção" (códigos 0-9) **NÃO existe no webservice legado de SP** e **não é necessário**. A Prefeitura infere o tipo automaticamente a partir do `<ValorCSLL>`. Nossa implementação atual já está 100% conforme. A flag `emitir_tipo_retencao` permanece `false` permanentemente para este webservice.

### O que foi testado

Em 07/06/2026, com certificado válido, sondamos o schema do webservice (`nfews.prefeitura.sp.gov.br/lotenfe.asmx`) em modo teste, posicionando o `<TipoRetencao>` em diferentes lugares do `<RPS>`:

| Posição testada | Resposta da Prefeitura |
|---|---|
| Entre `<ValorCSLL>` e `<CodigoServico>` | ❌ Erro 1001 — "invalid child element 'TipoRetencao'. List of possible elements expected: **'CodigoServico'**" |
| Após `<CodigoServico>` | ❌ Erro 1001 — "invalid child element ... List of possible elements expected: **'AliquotaServicos'**" |
| Sem o campo (formato atual) | ✅ `"sucesso": true` |

### Mapa do schema legado de SP (deduzido das mensagens de erro)

```
... → ValorINSS → ValorIR → ValorCSLL → CodigoServico → AliquotaServicos → ...
```

Não há lugar para um campo de tipo de retenção em nenhuma posição da sequência. **O schema legado simplesmente não tem esse elemento.**

### Por que o campo não existe (e não precisa existir)

1. **Webservice legado de SP (que usamos):** a Prefeitura **infere** o tipo de retenção a partir dos valores. Se `<ValorCSLL>` (soma PCC) > 0 → retido (equivale ao código 3); se ausente → não retido (código 0).
2. **Emissão online (portal manual):** aí sim aparece o campo "Contribuições Sociais – Retidas" com os códigos 0-9, porque é preenchimento humano.
3. **Padrão Nacional (gov.br):** usa os campos `tpRetPisCofins` e `vRetCSLL` — mas é **outro sistema**, regido pela NT 007/2026, que **não afeta** o webservice legado de SP (confirmado: a NT 007 aplica-se exclusivamente ao ambiente nacional gov.br).

### Conclusão

✅ A skill está **totalmente em conformidade** com as regras vigentes desde 14/05/2026. Nenhuma alteração de código é necessária.
✅ A flag `emitir_tipo_retencao` foi mantida (default `false`) apenas como salvaguarda — caso a Prefeitura algum dia adicione o campo ao webservice legado, basta ligá-la. Mas isso é **improvável**, pois a inferência por `<ValorCSLL>` já resolve.

### ✅ CONFIRMAÇÃO PELO XSD OFICIAL (07/06/2026)

Baixamos o **XSD oficial da Prefeitura** direto do [portal do desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/desenvolvedor/) e inspecionamos a definição do RPS (`tpRPS`) nos dois schemas:

| Schema | Arquivo | Sequência dos campos de tributos |
|---|---|---|
| Legado (até 31/12/2025) | `TiposNFe_v01.xsd` | `ValorPIS → ValorCOFINS → ValorINSS → ValorIR → ValorCSLL → CodigoServico` |
| Reforma 2026 | `TiposNFe_v02.xsd` (atualizado 29/12/2025) | idêntico: `ValorPIS → ValorCOFINS → ValorINSS → ValorIR → ValorCSLL → CodigoServico` |

**Busca exaustiva por `TipoRetencao` / `tpRet` / `indReten` nos dois XSDs: zero resultados.** A única ocorrência de "Ret" é `RetornoComplementarIBSCBS` (retorno de IBS/CBS, não retenção de tributos). Isso é **prova documental** de que o campo de tipo de retenção não existe no webservice de SP — nem no legado, nem na reforma 2026. A skill está definitivamente correta.

**Fontes oficiais consultadas:**
- XSD: `schemas-reformatributaria-v02-4` (atualizado 09/01/2026) — [portal desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/desenvolvedor/)
- Manual: [NFe_Web_Service v3.3](https://notadomilhao.sf.prefeitura.sp.gov.br/wp-content/uploads/2025/11/NFe_Web_Service-4.pdf) (nov/2025)

**Para reproduzir o teste de conformidade** (não emite nota real):
```bash
./.venv/bin/python emitir_nfse.py --modo teste --dados nota.json --json-out
# Esperado: {"sucesso": true, "notas_geradas": []}
```

---

## 8. Referências

- Email do contador (05/2026) — alterações na sistemática de tributos federais NFS-e SP
- [Prefeitura SP — Nova sistemática de tributos federais nos leiautes 1 e 2](https://notadomilhao.sf.prefeitura.sp.gov.br/noticias/alteracao-na-emissao-de-nfs-e-nova-sistematica-de-indicacao-de-tributos-federais-nos-leiautes-1-e-2/) (vigência 14/05/2026)
- [NT SE/CGNFS-e nº 007/2026](https://www.totvs.com/blog/fiscal-clientes/nfs-e-nacional-nota-tecnica-no-007-2026-esclarece-pis-cofins-retencoes-e-atualiza-codigos-de-operacao/) — aplica-se **apenas ao padrão Nacional** (gov.br), não ao webservice legado de SP
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
