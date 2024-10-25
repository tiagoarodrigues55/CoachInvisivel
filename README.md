# README - Script de Integração com Fireflies e OpenAI

## Descrição

Este script automatiza a coleta de transcrições de reuniões via API da Fireflies, processa os dados utilizando **Python** e **OpenAI**, e envia relatórios formatados por e-mail. Ele realiza análise de sentenças, identifica objeções e gera mensagens customizadas em HTML, que são convertidas em anexos para envio automático.

## Funcionalidades

- **Coleta de transcrições**: Utiliza a API da Fireflies para obter as últimas 10 transcrições de reuniões.
- **Processamento de dados**: Extrai informações relevantes e as organiza em um DataFrame.
- **Identificação de objeções**: Utiliza a API da OpenAI para identificar objeções nas conversas.
- **Geração de e-mails personalizados**: Cria relatórios em HTML com base nas transcrições.
- **Envio automático de e-mails**: Envia os relatórios para destinatários correspondentes.
  
---

## Requisitos

- **Python 3.x**
- **Pacotes**:
  - `requests`
  - `pandas`
  - `openai`
  - `yagmail`
  - `json`
  - `datetime`
  - `os`
  - `re`

Instale as dependências executando:
```bash
pip install requests pandas openai yagmail
```

---

## Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no seu sistema para garantir o funcionamento:

- **OPENAI_API_KEY**: Chave de API da OpenAI.
- **FIRELIES_API_KEY**: Chave de API da Fireflies.
- **EMAIL_PASSWORD**: Senha do e-mail utilizado para envio de relatórios.

Adicione-as no terminal:
```bash
export OPENAI_API_KEY='sua-chave-aqui'
export FIRELIES_API_KEY='sua-chave-aqui'
export EMAIL_PASSWORD='sua-senha-aqui'
```

---

## Estrutura do Código

1. **Consulta à API Fireflies**:
   - Recupera as últimas 10 transcrições.
   - Filtra as transcrições pelo período dos últimos 7 dias.

2. **Processamento dos Dados**:
   - Converte datas para o fuso horário de Brasília.
   - Verifica nomes dos participantes e associa e-mails através do arquivo `users.xlsx`.

3. **Análise com OpenAI**:
   - Extrai objeções das sentenças utilizando a API da OpenAI.

4. **Geração de Relatórios HTML**:
   - Formata as informações em HTML.
   - Converte texto em negrito para tags `<b>`.

5. **Envio de E-mails**:
   - Utiliza `yagmail` para enviar os relatórios por e-mail.
   - Os dados processados são salvos em `transcripts.xlsx`.

---

## Como Utilizar

1. **Preparar os arquivos de entrada**:
   - `ids.xlsx`: Arquivo contendo os IDs já processados.
   - `users.xlsx`: Arquivo com mapeamento de nomes e e-mails dos participantes.

2. **Executar o script**:
   - Execute o script no terminal:
     ```bash
     python seu_script.py
     ```

3. **Verificação e envio**:
   - Se houver novas transcrições, os e-mails serão enviados automaticamente.
   - O arquivo `ids.xlsx` será atualizado com os novos registros.

---

## Exemplo de Saída

- **HTML Gerado**:
  - Resumo principal da reunião.
  - Lista de objeções identificadas.
  - Itens de ação e próximos passos.

- **Arquivo Final**:
  - `transcripts.xlsx`: Consolidado das transcrições e informações relevantes.

---

## Possíveis Erros e Soluções

- **Erro de autenticação**: Verifique as chaves de API nas variáveis de ambiente.
- **Erro ao enviar e-mails**: Confirme a senha e permissões da conta de e-mail.
- **Transcrições ausentes**: Certifique-se de que o período consultado possui reuniões registradas.

---

## Contato

Em caso de dúvidas ou sugestões, entre em contato pelo e-mail **admin@coachinvisivel.com**.