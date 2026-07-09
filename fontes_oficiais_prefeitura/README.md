# Fontes Oficiais — Prefeitura de São Paulo (NFS-e)

Arquivos oficiais baixados do portal da Prefeitura de SP, arquivados aqui para referência de implementação e auditoria. **Snapshot baixado em 07/06/2026.**

> ⚠️ Estes são documentos **públicos** da Prefeitura (não contêm dados do contribuinte). São a fonte normativa para qualquer alteração na skill.

## 📂 Arquivos neste diretório

| Arquivo | Origem oficial | Atualizado em (origem) | O que contém |
|---|---|---|---|
| `NFe_WebService_v3.3_nov2025.pdf` | [Portal Desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/wp-content/uploads/2025/11/NFe_Web_Service-4.pdf) | nov/2025 (v3.3) | Manual do WebService — endpoints, métodos, campos, mensagens de erro, layouts v1 e v2 |
| `schemas-reformatributaria-v02-4.zip` | [Portal Desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/schemas-reformatributaria-v02-4/) | 09/01/2026 | XSDs do **Layout 2** (Reforma Tributária 2026, com grupo IBSCBS) |
| `schemas-legado-v01-1.zip` | [Portal Desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/wp-content/uploads/2025/09/schemas-v01-1.zip) | set/2025 | XSDs do **Layout 1** legado (síncrono, vigente até 31/12/2025; ainda aceito em 2026) |
| `schemas-assincrono-v01-1.zip` | [Portal Desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/wp-content/uploads/2025/09/schemas-assincrono-v01-1.zip) | set/2025 | XSDs dos serviços **assíncronos** (LoteNFeAsync) |

## 🌐 Portais oficiais (para checar atualizações)

- **Portal do Desenvolvedor:** https://notadomilhao.sf.prefeitura.sp.gov.br/desenvolvedor/
- **Manuais:** https://notadomilhao.sf.prefeitura.sp.gov.br/manuais/
- **Reforma Tributária (Fazenda):** https://prefeitura.sp.gov.br/web/fazenda/w/nfs-e_orientacoes

## 🔌 Endpoints do WebService (conforme manual v3.3)

| Endpoint | URL | Observação |
|---|---|---|
| Síncrono **antigo** | `https://nfe.prefeitura.sp.gov.br/ws/lotenfe.asmx` | ⚠️ **Não comporta** o novo layout (v2) |
| Síncrono **novo** ✅ | `https://nfews.prefeitura.sp.gov.br/lotenfe.asmx` | **Comporta ambos os layouts (v1 e v2)** — é o que a skill usa |
| Assíncrono | `https://nfews.prefeitura.sp.gov.br/lotenfeasync.asmx` | Serviços assíncronos (LoteNFeAsync) |

## 📌 Achados-chave desta documentação (07/06/2026)

1. **`TipoRetencao` não existe no webservice** (nem v1 nem v2). Confirmado por busca exaustiva nos XSDs. O campo de tipo de retenção só existe na emissão online (portal) e no padrão Nacional gov.br. → Ver `SP_PCC_2026.md` seção 7.

2. **Layout 2 (IBSCBS) já está totalmente publicado** — endpoint e schema disponíveis. O RPS v02 tem estrutura própria (sem `<ValorServicos>`, com grupo `<IBSCBS>` obrigatório e novos campos como `NBS`, `ValorIPI`). → Ver `MIGRATION_RTC_2026.md` (branch `rtc-2026-layout-v2`).

3. **2026 continua sem recolhimento obrigatório** de CBS/IBS (LC 214/2025). O Layout 1 com a sistemática PCC (já implementada na `main`) segue plenamente válido.

## 🔄 Como re-baixar / atualizar estas fontes

```bash
# Manual WebService
curl -L "https://notadomilhao.sf.prefeitura.sp.gov.br/wp-content/uploads/2025/11/NFe_Web_Service-4.pdf" -o NFe_WebService_atual.pdf

# Schemas Reforma 2026
curl -L "https://notadomilhao.sf.prefeitura.sp.gov.br/schemas-reformatributaria-v02-4/" -o schemas-reformatributaria.zip

# Schemas legado
curl -L "https://notadomilhao.sf.prefeitura.sp.gov.br/wp-content/uploads/2025/09/schemas-v01-1.zip" -o schemas-legado.zip
```

Sempre confira no [portal do desenvolvedor](https://notadomilhao.sf.prefeitura.sp.gov.br/desenvolvedor/) se há versão mais recente antes de implementar mudanças.
