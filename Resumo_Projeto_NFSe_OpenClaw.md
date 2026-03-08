# Resumo do Projeto: Emissor de NFS-e São Paulo (API SOAP)

Este documento resume a infraestrutura contruída até o momento para viabilizar a emissão automatizada de Notas Fiscais Eletrônicas de Serviço na Prefeitura de São Paulo via Python e OpenClaw.

## 🏗️ 1. Arquitetura Consolidada
O projeto roda perfeitamente em 3 camadas desacopladas:
*   **Engine Criptográfica (`emitir_nfse.py`):** Resolve os complexos cálculos do modelo A1 (XMLDSig e Hash Interno RSA-SHA1 exigidos pela PMSP). Possui uma flag `--json-out` para comunicação silenciosa M2M. Possui suporte a `--modo teste` e `--modo producao`.
*   **Parametrização Passiva (`config.json`):** Arquivo estático contendo as regras base da empresa emissora (Inscrição Municipal, CNPJ, Código do Serviço Médico = 04030, Tributação = T, e Série do RPS = "XY").
*   **Orquestração por IA (OpenClaw):** Agente parametrizado pelas regras descritas em `Instrucoes_OpenClaw.md`. O agente possui a responsabilidade isolada de construir o payload preenchido da nf daquele cliente (`dados_nota.json`) e de executar o CLI para gerar a NFS-e.

## 🔐 2. Segurança e Controle (Umbrel-Ready)
*   **Senha do Certificado Oculta:** Para sobreviver aos expurgos do Docker/Umbrel sem expor a senha em texto plano `config.json`, criamos um arquivo solto `.env` contendo `NFSE_CERT_PASSWORD="<senha>"`. O script Python possui o pacote `python-dotenv` instalado para mapear o arquivo secretamente no tempo de execução.
*   **Controle Lógico do Incrementador RPS:** Uma vez que a Prefeitura não devolve via chamada de "Busca" retroativa da API qual foi o último RPS emitido via web, construímos a série isolada `XY` explusiva do Robô.
*   Conforme as diretrizes, o OpenClaw deve ler um arquivo nativo `contador_rps.txt` começando do "1", incrementar +1 ali dentro ao emitir a nota, e fechar a sessão para impedir a colisão com notas manuais emitidas no antigo ambiente web da Receita (Série A/B etc).

## 🚀 3. Estado Atual e Próximos Passos
O núcleo tecnológico e as chaves sistêmicas (inclusive a validação do SP-1057 de hashes XML que trazia um falso positivo na POC) estão **100% resolvidos, auditados e prontos em terminal.** O script também já foi auditado para disparar a Nota por Email automaticamente pelo sistema da Prefeitura caso a tag `<EmailTomador>` seja preenchida pela IA. 

O que falta para a Nova Reunião / Sessão:
*   **Regras de Negócio Puras:** Ajustar o "Como preencher" o corpo visual da Nota. 
*   Quais serão as mensagens de discriminação padrão (ex: Isenções, Descrições Médicas Específicas).
*   Revisão matemática das alíquotas (Impostos Retidos como PIS, COFINS, tabelas etc).
*   Testar a primeira emissão real no modo de Produção Oficial com essas novas regras finas.
