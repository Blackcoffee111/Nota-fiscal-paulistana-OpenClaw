# Branch `rtc-2026-layout-v2` — Reforma Tributária do Consumo

> **Para usuário não-técnico:** esta branch contém código **experimental** preparando a skill para o novo formato da NFS-e SP (com IBS e CBS). **Não está em uso na emissão real.** A produção continua na branch `main` com `emitir_nfse.py` v1, que segue 100% válido durante todo o ano de 2026.

## Como navegar entre as duas versões

```bash
# Ver branch atual
git branch --show-current

# Voltar para a versão de produção (sem IBS/CBS)
git checkout main

# Voltar para o experimento RTC
git checkout rtc-2026-layout-v2
```

## Arquivos desta branch (não existem em main)

| Arquivo | Função |
|---|---|
| `NT_04_v2.pdf` | Nota Técnica 004 v1.1 oficial — especificação federal do grupo IBSCBS |
| `MIGRATION_RTC_2026.md` | Diff técnico completo: cronograma, todos os campos novos do XML, regras 2026 vs 2027+, resultado do teste real contra a Prefeitura |
| `emitir_nfse_v2.py` | Scaffold do emissor com grupo IBSCBS injetado (a partir do v1) |
| `RTC_2026_README.md` | Este arquivo |

## Arquivos modificados

- `config.json` — bloco `ibscbs` adicionado (com `habilitado: false` por padrão)

## Resumo do que foi descoberto no teste real

Executamos `emitir_nfse_v2.py --modo teste` (modo validação, **não emite nota real**) contra o webservice da Prefeitura SP. Resposta: **erro 1001** — o webservice atual rejeita o grupo `<IBSCBS>`. Isso confirma que:

1. O endpoint legado **`lotenfe.asmx`** segue só com Layout 1
2. A Prefeitura SP ainda não publicou o endpoint do Layout 2
3. Para 2026, **a emissão real continua perfeita no `emitir_nfse.py` v1** — a LC 214/2025 dispensa recolhimento de CBS/IBS neste ano

## Próximo passo (quando aplicável)

Quando a Prefeitura SP divulgar o novo endpoint Layout 2:
1. `git checkout rtc-2026-layout-v2`
2. Atualizar URL em `emitir_nfse_v2.py` (linha do `url = "https://..."`)
3. Confirmar posição do `<IBSCBS>` no XSD oficial (TODO marcado no código)
4. Confirmar com contador os códigos `CST` e `cClassTrib` reais para serviço médico (04030)
5. Testar com `--modo teste` antes de mergear em main
