# Robô de Notas Fiscais (NFS-e São Paulo) para OpenClaw

Bem-vindo! Este pacote de arquivos foi criado para dar ao seu assistente virtual (OpenClaw) o "superpoder" de emitir, cancelar e baixar relatórios de Notas Fiscais diretamente no sistema da Prefeitura de São Paulo.

Você não precisa ser um programador para usar. Siga este passo a passo simples usando palavras do dia a dia para configurar sua clínica/empresa!

---

## 🛠️ Instalação Passo a Passo (Para Leigos)

### 1. Onde colocar a pasta do projeto?
Para que o seu robô (OpenClaw) entenda e adote essas funções financeiras, você deve colocar todos estes arquivos dentro da "Central de Habilidades" (Skills) do seu Agente.
- Geralmente, fica na pasta `workspace/skills/` (por exemplo: crie uma pasta chamada `faturamento_sp` lá dentro e jogue todos os arquivos nela).

### 2. A Mágica do "Wizard Automático" (Mais Fácil! ✨)
Sabe a parte chata de configurar arquivos cheios de códigos e números? **O seu robô agora faz isso por você!**
Nós programamos um *Assistente de Instalação (Wizard)* embutido.

Se você não quer mexer em nenhum arquivo de texto, basta fazer o seguinte:
1. Abra o chat do seu OpenClaw.
2. Diga a ele algo como: *"Emita uma Nota"* ou *"Preciso testar a skill de nota fiscal"*.
3. **Imediatamente**, o robô perceberá que este é seu primeiro acesso e iniciará os preparativos:
    *   **Auto-Instalação:** Ele rodará as ferramentas necessárias automaticamente para garantir que seu Python esteja pronto.
    *   **Entrevista:** Ele perguntará pelo chat o seu CNPJ, Inscrição Municipal, Código de Serviço e a sua **Alíquota de ISS** (Se você não souber o imposto, ele pesquisa no Google para você!).
    *   **Segurança:** Ele criará o arquivo secreto para a sua senha e pedirá para você preenchê-lo manualmente por segurança.
4. **Respeito à Privacidade:** O robô nunca lê a sua senha no arquivo `.env`. Ele confia que você a inseriu e pula direto para a validação!

---

### 3. O Passo Final: O "Batismo de Fogo" 🔥
Assim que você configurar seu Certificado e Senha (conforme os Passos 4 e 5 abaixo), o robô não encerrará a conversa até realizar um **Faturamento de Teste Real de R$ 150,00**. 
- Isso serve para garantir que a sua assinatura digital está funcionando perfeitamente e que a prefeitura de São Paulo aceita a sua conexão. Só depois desse teste bem-sucedido é que o sistema é liberado para notas reais!

---

### 4. Onde coloco o meu Certificado Digital?
Você precisará do seu certificado digital (aquele arquivo `.p12` ou `.pfx` concedido pelo governo ou seu contador).
- Pegue o seu próprio arquivo e **cole-o dentro da pasta** onde estão o resto dos arquivos do projeto. O robô perguntará o nome do arquivo para você lá no chat para salvar no seu perfil!

### 5. Onde eu coloco a SENHA do meu Certificado?
No mundo dos desenvolvedores, colocar senha mestra diretamente no chat ou em arquivos tradicionais é perigoso. Por isso, a sua senha vai morar num arquivo "secreto" e seguro chamado **`.env`** (Sim, ele começa com um ponto final mesmo!).

- Abra esse arquivo `.env` usando o Bloco de Notas ou o editor de texto do seu computador.
- Você verá um texto assim: `NFSE_CERT_PASSWORD=SUA_SENHA_AQUI_NAO_COLOQUE_NO_GITHUB`
- Apague toda a frase da direita e digite a sua verdadeira senha **colada** ao sinal de Igual `=`.
- Ficará assim: `NFSE_CERT_PASSWORD=senha123` (Salve e feche).

*(Dica: Computadores Mac costumam esconder da sua visão arquivos que começam com um ponto. Se você não estiver vendo o `.env` ou o `.gitignore`, aperte `Command + Shift + .` (Ponto) para o seu Mac revelar os arquivos ocultos!)*

---

### ⚠️ Método Alternativo: Configuração Manual (Para usuários avançados)
Se, por qualquer motivo, você não quiser conversar com o robô para ele preencher os dados, você pode fazer "na mão":
- Abra o arquivo **`config.json`**.
- Troque os campos `"MEUCNPJ"`, `"Minhainscricao"`, `"Meucodigo"`, e `"MEUCertificado.p12"` pelos seus dados reais.
- No campo `"aliquota_servicos"`, use o formato decimal (ex: `0.02` para 2%).

### 🚀 6. Pronto pra Voar!
A sua personalização está 100% terminada.
Agora, no seu OpenClaw, o arquivo "Mestre" robótico chamado `SKILL.md` fará o elo do sistema.

Basta abrir a janela de chat do robô e dizer: *"Emita uma Nota de R$ 38.000,00 para a Clínica Exemplo usando a skill de nota fiscal!"*. A IA resgatará este manual, lerá os seus bloqueios e as senhas nas sombras e lhe devolverá pelo próprio chat o Link definitivo e impresso com sucesso validado em São Paulo!
