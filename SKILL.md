---
description: Faturamento NFS-e SP (Emissão e Cancelamento de Notas Fiscais em São Paulo)
---

# Habilidade de Faturamento NFS-e SP (OpenClaw)

Esta documentação define o comportamento e as arquiteturas da Skill de faturamento para emitir e cancelar Notas Fiscais de Serviços Eletrônica (NFS-e) da Prefeitura de São Paulo.

> **Importante:** Todos os arquivos descritos abaixo devem estar contidos na mesma pasta desta Skill (ex: `workspace/skills/nfse-sp/`).

## 📁 Arquivos do Ecossistema
1. `emitir_nfse.py` - Script de emissão em produção (gera o XML SOAP, encripta e envia).
2. `cancelar_nfse.py` - Script de cancelamento de notas (criptografa o cancelamento).
3. `config.json` - Retenções e alíquotas da clínica (ex: ISS, IRRF, limites, etc).
4. `tomadores.json` - Tabela de dados de clientes recorrentes (sua agenda).
5. `contador_rps.txt` - Arquivo de controle rigoroso para a sequência do talão.
6. `Certificados.p12` - Chave criptográfica municipal (JAMAIS EXPOR).
7. `.env` - Arquivo oculto onde você lerá a variável `NFSE_CERT_PASSWORD=senha`.
8. `baixar_notas.py` - Script paginado de extração de relatórios e balanços contábeis da clínica.

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
Siga as 6 etapas abaixo sempre que o usuário solicitar emissão:

**1. Recepção de Pedido:** O usuário pedirá a nota (Valor e Tomador). Ex: "Nota de 1500 para a AMIL".
**2. Triagem Local (`tomadores.json`):** Leia o arquivo `tomadores.json` em background. Se o Tomador já estiver cadastrado, puxe o CNPJ, endereço e e-mail de lá. Se for inédito, peça ao usuário os dados faltantes.
**3. Simulação Financeira (Draft):** Calcule os impostos internamente cruzando com as regras do `config.json`. Responda ao usuário com um "Esboço" detalhado (Valor Bruto, valor de cada retenção aplicada, Total Líquido e Preview da Discriminação da nota).
**4. Oitiva Humana:** Pergunte se o usuário "Aprova o Faturamento".
**5. Emissão e RPS:** 
   * Se aprovado, leia `contador_rps.txt` para pegar o próximo número sequencial X.
   * Gere o arquivo `/tmp/dados_rps_X.json` autônomamente.
   * Execute: `python emitir_nfse.py --modo producao --dados /tmp/dados_rps_X.json --json-out`
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
  "calcular_retencoes": true,
  "valor_servicos": 150.00,
  "indicador_tomador": 2, // 2 para CNPJ, 1 para CPF, 3 para Sem Identificação
  "documento_tomador": "<Apenas_Numeros>",
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
