# Migração NFS-e SP — Reforma Tributária do Consumo (2026+)

Branch: `rtc-2026-layout-v2`
Base normativa:
- **EC nº 132/2023** (Reforma Tributária do Consumo)
- **LC nº 214, 16/01/2025** (regulamentação da CBS, IBS, IS)
- **NT 04 SE/CGNFS-e v1.1** (19/08/2025) — `NT_04_v2.pdf` na raiz da skill
- **Informe Técnico RT 2025.002 v1.10** (tabelas CST / cClassTrib / cCredPres)
- **AnexoVII-IndOp_IBSCBS_V1.00.00.xlsx** (códigos de indicador de operação)

---

> ## 🆕 ATUALIZAÇÃO 07/06/2026 — A PREFEITURA SP JÁ PUBLICOU TUDO!
>
> Reavaliação com as **fontes oficiais da Prefeitura** ([portal do desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/desenvolvedor/) + [manual do webservice v3.3](https://notadomilhao.sf.prefeitura.sp.gov.br/wp-content/uploads/2025/11/NFe_Web_Service-4.pdf)) mudou o quadro. **O Layout 2 saiu do "aguardando" para o "implementável agora".**
>
> ### O que mudou desde a conclusão original (seção 6 abaixo)
>
> A conclusão antiga dizia "endpoint distinto, ainda não divulgado". **Estava errada.** A verdade oficial:
>
> | Item | Status real (fonte oficial) |
> |---|---|
> | **Endpoint do Layout 2** | ✅ **É o mesmo que já usamos**: `https://nfews.prefeitura.sp.gov.br/lotenfe.asmx`. O manual diz textualmente: *"Este novo endereço do serviço síncrono comporta ambos os layouts (versão 1 e 2). Recomendamos a mudança para este endereço."* |
> | **Schema oficial do Layout 2** | ✅ **Publicado**: `schemas-reformatributaria-v02-4` (atualizado 09/01/2026). Cópia salva em `schemas_oficiais_sp/`. |
> | **Grupo `<IBSCBS>`** | ✅ Existe no schema oficial (`tpIBSCBS`, `tpGIBSCBS`) e é **obrigatório** (`minOccurs=1`) dentro do RPS v02. |
> | **Por que o teste anterior deu erro 1001** | Porque injetamos `<IBSCBS>` na estrutura do **Layout 1**. O Layout 2 tem estrutura de RPS **diferente** e exige `<VersaoSchema>2`. |
>
> ### ⚠️ Diferenças críticas do RPS v02 (descobertas no XSD oficial)
>
> O `tpRPS` do schema v02 **NÃO é o v01 + IBSCBS**. É uma estrutura nova:
> - ❌ **`<ValorServicos>` não existe** no v02 (o manual confirma explicitamente)
> - ✅ Campos de retenção **obrigatórios** (`minOccurs=1`): `ValorPIS, ValorCOFINS, ValorINSS, ValorIR, ValorCSLL`
> - ✅ Novos campos **obrigatórios**: `ValorIPI`, `NBS` (código), `ExigibilidadeSuspensa`, `PagamentoParceladoAntecipado`
> - ✅ Grupo `<IBSCBS>` obrigatório no fim do RPS (com `CST`, `cClassTrib`, valores, etc.)
> - ✅ Novos campos opcionais: `NCM`, `atvEvento`, `gpPrestacao`, `ChaveNotaNacional`
>
> **Consequência:** o scaffold atual `emitir_nfse_v2.py` (que apenas injeta `<IBSCBS>` no XML v1) **não serve** — precisa ser reescrito para montar o RPS v02 do zero, seguindo `schemas_oficiais_sp/TiposNFe_v02.xsd`.
>
> ### O que falta para implementar (não é mais bloqueio externo!)
>
> Tudo que falta agora é **trabalho de implementação nosso** — a Prefeitura já fez a parte dela:
> 1. Reescrever `emitir_nfse_v2.py` para a estrutura completa do RPS v02 (ver XSD em `schemas_oficiais_sp/`)
> 2. Enviar com `<VersaoSchema>2` no envelope SOAP
> 3. Preencher o grupo `<IBSCBS>` obrigatório (CST, cClassTrib — confirmar códigos com contador para serviço 04030)
> 4. Preencher os novos campos obrigatórios (NBS, ValorIPI=0, ExigibilidadeSuspensa, etc.)
> 5. Testar com `--modo teste` no mesmo endpoint
>
> **Continua sem urgência fiscal:** a LC 214/2025 dispensa o recolhimento de CBS/IBS em 2026. Mas agora é uma **decisão de quando implementar**, não mais uma espera pela Prefeitura. Marco para ter pronto: **01/01/2027**.
>
> **Sobre o `<TipoRetencao>` (PCC):** confirmado pelo XSD oficial que **não existe** em nenhum schema (v01 nem v02). A frente PCC 2026 na `main` está 100% correta. Ver `SP_PCC_2026.md` seção 7 na branch main.

---

## 1. Cronograma e regras de transição

| Período | CBS | IBS | PIS/COFINS | ISS |
|---|---|---|---|---|
| **2026** (ano-teste) | 0,9% (informativo) | 0,1% (informativo) | normal | normal |
| **2027** | alíquota cheia, recolhimento | 0,1% | **extintos** | normal |
| **2028** | alíquota cheia | 0,1% | — | normal |
| **2029-2032** | cheia | redução gradual ISS → IBS (10% a.a.) | — | reduzindo |
| **2033** | cheia | 100% IBS | — | extinto |

**Em 2026:** quem cumprir as obrigações acessórias (emitir no layout v2 com grupo IBSCBS preenchido) está **dispensado do recolhimento** de CBS/IBS. Os valores são calculados e destacados, mas não somam no `vTotNF` da nota — apenas a partir de 2027.

> Fórmula da NT 04, seção 2.2.3:
> - `vTotNF = vLiq` (em 2026)
> - `vTotNF = vLiq + vCBS + vIBSTot` (a partir de 2027)

---

## 2. Diff de campos: Layout v1 → Layout v2

### 2.1 Novo grupo na DPS — caminho `NFSe/infNFSe/DPS/infDPS/IBSCBS/`

| Campo | Tipo | Ocor. | Tam. | Descrição |
|---|---|---|---|---|
| `IBSCBS` | G | 1-1 | — | Grupo de informações IBS/CBS (raiz) |
| `finNFSe` | N | 1-1 | 1 | 0=regular, 1=crédito, 2=débito |
| `indFinal` | N | 1-1 | 1 | 0=Não, 1=Sim (uso/consumo pessoal) |
| `cIndOp` | N | 1-1 | 6 | Código indicador de operação (Anexo VII) |
| `tpOper` | N | 0-1 | 1 | Operação com ente governamental |
| `tpEnteGov` | N | 0-1 | 1 | 1=União, 2=Estado, 3=DF, 4=Município, 9=Outro |
| `gRefNFSe/refNFSe` | C | 0-1 | 50 | Chave de NFS-e referenciada |
| `indDest` | N | 1-1 | 1 | 0=tomador é destinatário; 1=destinatário distinto |

### 2.2 Subgrupo `dest/` — destinatário do serviço (quando ≠ tomador)

| Caminho | Campo | Tipo | Ocor. | Obs |
|---|---|---|---|---|
| `IBSCBS/dest/` | `CNPJ` ou `CPF` ou `NIF` | CE | 1-1 | choice |
| `IBSCBS/dest/` | `xNome` | C | 1-1 | até 150 |
| `IBSCBS/dest/end/endNac/` | `cMun` | N | 1-1 | 7 (IBGE) |
| `IBSCBS/dest/end/endNac/` | `CEP` | C | 1-1 | 8 |
| `IBSCBS/dest/end/` | `xLgr`, `nro`, `xBairro` | C | 1-1 | endereço |
| `IBSCBS/dest/` | `email` | C | 0-1 | até 80 |

### 2.3 Subgrupo `imovel/` (serviços sobre bem imóvel, exceto obra)

`IBSCBS/imovel/` com `inscImobFisc` ou `cCIB`, e endereço completo.

### 2.4 Subgrupo `valores/trib/gIBSCBS/` — **CST e cClassTrib (obrigatórios)**

| Campo | Tipo | Ocor. | Tam. | Descrição |
|---|---|---|---|---|
| `CST` | N | 1-1 | 3 | Código de Situação Tributária IBS/CBS |
| `cClassTrib` | C | 1-1 | 6 | Código de Classificação Tributária |
| `cCredPres` | N | 0-1 | 2 | Crédito presumido (quando aplicável) |
| `gTribRegular/CSTReg`, `cClassTribReg` | — | 0-1 | — | Quando há tributação regular paralela |
| `gDif/pDifUF`, `pDifMun`, `pDifCBS` | N | 0-1 | 1-3V2 | Percentuais de diferimento |

### 2.5 Subgrupo `valores/gReeRepRes/` — reembolsos e ressarcimentos
Documenta valores a serem deduzidos da base de cálculo (referência cruzada a NF-e/NFS-e/CT-e do Repositório Nacional).

---

## 3. Grupo `IBSCBS` na NFS-e (calculado pela plataforma — não preencher)

A Sefin Nacional preenche esses campos; constam na nota retornada.

### 3.1 `NFSe/infNFSe/IBSCBS/`
- `cLocalidadeIncid` (cód IBGE), `xLocalidadeIncid`, `pRedutor`

### 3.2 `IBSCBS/valores/`
- **`vBC`** (base de cálculo):
  - 2026: `vBC = vServ - descIncond - vCalcReeRepRes - vISSQN - vPIS - vCOFINS`
  - até 2032: `vBC = vServ - descIncond - vCalcReeRepRes - vISSQN`
- `valores/uf/`: `pIBSUF`, `pRedAliqUF`, `pAliqEfetUF`
- `valores/mun/`: `pIBSMun`, `pRedAliqMun`, `pAliqEfetMun`
- `valores/fed/`: `pCBS`, `pRedAliqCBS`, `pAliqEfetCBS`

### 3.3 Totalizadores `IBSCBS/totCIBS/`
- `vTotNF` (regra 2026 vs 2027+ — ver §1)
- `gIBS/vIBSTot = vIBSUF + vIBSMun`
- `gCBS/vCBS = vBC × pCBS`
- Subgrupos `gIBSUFTot`, `gIBSMunTot`, com diferimentos `vDifUF`, `vDifMun`, `vDifCBS`
- `gIBSCredPres`, `gCBSCredPres` para créditos presumidos

---

## 4. Mudanças aplicadas nesta branch

### 4.1 `config.json` — novo bloco `ibscbs`
```json
"ibscbs": {
  "habilitado": false,
  "fin_nfse": 0,
  "ind_final": 0,
  "c_ind_op": "111111",
  "ind_dest": 0,
  "cst": "000",
  "cclasstrib": "000001",
  "ccredpres": null,
  "aliquota_cbs": 0.009,
  "aliquota_ibs_uf": 0.001,
  "aliquota_ibs_mun": 0.000
}
```
Mantém `habilitado: false` por padrão — o `emitir_nfse.py` continua emitindo no layout v1 sem alterações. Para usar v2: `habilitado: true` + chamar `emitir_nfse_v2.py`.

### 4.2 `emitir_nfse_v2.py` — scaffold do layout v2
- Importa as funções de `emitir_nfse.py` (assinatura, envio SOAP, parsing)
- Sobrescreve `construir_xml_lote` para injetar o grupo `<IBSCBS>` após `</Discriminacao>`
- Calcula CBS/IBS/IBS-Mun com as alíquotas-teste de 2026
- Suporta destinatário distinto do tomador (`indDest=1`)
- Mantém `--dry-run`, `--modo teste|producao`, `--json-out`

### 4.3 Pendências marcadas como `TODO_SP_LAYOUT_V2`
1. **Posição exata do `<IBSCBS>` no envelope SP** — está provisoriamente após `</Discriminacao>`. Confirmar contra o XSD oficial do Layout 2 da Prefeitura SP quando disponibilizado.
2. **Versão do schema SOAP** — atual usa `<VersaoSchema>1</VersaoSchema>`; provavelmente passa a `2` no layout v2.
3. **Endpoint do webservice** — verificar se `lotenfe.asmx` aceita o layout v2 ou se há URL distinta.
4. **Tabelas CST e cClassTrib** — os códigos default (`000` / `000001`) são placeholders; cruzar o código de serviço 04030 (médico/profissão regulamentada) com o Informe Técnico RT 2025.002 v1.10 para obter o código correto.

---

## 5. Roteiro de validação (antes de subir para `main`)

1. **Dry-run com IBSCBS desabilitado** — deve gerar XML idêntico ao v1:
   ```bash
   ./.venv/bin/python emitir_nfse_v2.py --modo teste --dados /tmp/test.json --dry-run
   ```
2. **Dry-run com IBSCBS habilitado** — inspecionar o `<IBSCBS>` injetado:
   ```bash
   # Editar config.json: "habilitado": true
   ./.venv/bin/python emitir_nfse_v2.py --modo teste --dados /tmp/test.json --dry-run
   ```
3. **Modo teste real (homologação SP)** — esperar `Sucesso: true` e validar resposta:
   ```bash
   ./.venv/bin/python emitir_nfse_v2.py --modo teste --dados /tmp/test.json --json-out
   ```
4. **Confirmar com o contador** os códigos `CST` e `cClassTrib` aplicáveis ao código de serviço 04030 antes de mudar `habilitado: true` em produção.
5. **Atualizar `SKILL.md`** com referência ao layout v2 e fluxo de escolha (v1 vs v2).

---

## 6. Resultado do teste real contra homologação SP (06/05/2026)

Executado: `./.venv/bin/python emitir_nfse_v2.py --modo teste --dados /tmp/test_emissao_10.json --json-out` com `ibscbs.habilitado=true`.

**Resposta da Prefeitura:**
```json
{
  "sucesso": false,
  "erros": [{
    "codigo": "1001",
    "descricao": "XML não compatível com Schema. The element 'RPS' has invalid child element 'IBSCBS'. List of possible elements expected: 'ValorCargaTributaria, PercentualCargaTributaria, FonteCargaTributaria, CodigoCEI, MatriculaObra, MunicipioPrestacao, NumeroEncapsulamento, ValorTotalRecebido'."
  }]
}
```

### Conclusões do teste

| Componente | Status |
|---|---|
| Conexão SOAP/TLS com `nfews.prefeitura.sp.gov.br/lotenfe.asmx` | ✅ OK |
| Autenticação por certificado mTLS | ✅ OK |
| Assinatura XMLDSig SHA-1 | ✅ Aceita |
| Schema do webservice atual | ❌ **Rejeita `<IBSCBS>`** (erro 1001) |

**Conclusão técnica:** o endpoint legado `lotenfe.asmx` segue restrito ao **Schema v1**. A Prefeitura de SP **não habilitou o grupo `<IBSCBS>` neste webservice**. O "Layout 2" RTC provavelmente exige:

1. **Endpoint distinto** (URL com versionamento, ainda não divulgada publicamente em 05/2026), **ou**
2. Integração via **padrão nacional Sefin** em `gov.br/nfse` (ambiente RTC de produção restrita atualizado em 10/12/2025)

### Implicação operacional para 2026

✅ **Continuar emitindo no Layout v1 (`emitir_nfse.py`) sem qualquer alteração.**
A LC 214/2025 art. 343-348 dispensa o recolhimento de CBS/IBS em 2026 mesmo sem destaque na NF-e — não há prejuízo fiscal por não usar o Layout v2 enquanto o endpoint não for liberado.

O scaffold `emitir_nfse_v2.py` fica como **base pronta** — quando o endpoint v2 for publicado, basta:
1. Atualizar a URL em `emitir_nota_v2` (override do `lotenfe.asmx`)
2. Confirmar a posição exata do `<IBSCBS>` no XSD oficial
3. Trocar `<VersaoSchema>1</VersaoSchema>` por `2`

---

## 7. Referências

- [NT 04 v2.0 (RTC) — gov.br/nfse](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-004-se-cgnfse-novo-layout-rtc.pdf) (PDF salvo em `NT_04_v2.pdf`)
- [Reforma Tributária — Nota Fiscal Paulistana](https://notadomilhao.sf.prefeitura.sp.gov.br/reforma-tributaria/)
- [Orientações NFS-e SP a partir de 01/01/2026](https://prefeitura.sp.gov.br/web/fazenda/w/nfs-e_orientacoes)
- [LC 214/2025 — Planalto](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm)
- [Tabela cClassTrib, CST, cCredPres — TecnoSpeed](https://blog.tecnospeed.com.br/tabela-cclasstrib/)
