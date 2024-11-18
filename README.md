# Projeto: Coach Invisível - Processamento e Envio de Transcritos

## Visão Geral
Este projeto tem como objetivo processar transcritos de reuniões, analisar seus conteúdos e gerar relatórios detalhados para envio automatizado via e-mail. Utiliza integração com a API Fireflies.ai, OpenAI, Supabase e Yagmail para automação e gerenciamento de dados.

## Funcionalidades Principais
- Consulta e processamento de transcritos via API Fireflies.ai.
- Integração com a OpenAI para identificação de objeções e soft skills.
- Gerenciamento de usuários e transcritos em um banco de dados Supabase.
- Geração de relatórios detalhados em HTML e envio automatizado de e-mails via Yagmail.

## Tecnologias Utilizadas
- **Linguagem**: Python
- **APIs**: Fireflies.ai, OpenAI
- **Banco de Dados**: Supabase
- **Envio de E-mail**: Yagmail
- **Outros**: Pandas, Requests, os (variáveis de ambiente)

## Configuração do Ambiente

1. **Instale as dependências**:
   ```bash
   pip install requests pandas openai yagmail supabase
   ```

2. **Configuração de variáveis de ambiente**:
   Crie um arquivo `.env` na raiz do projeto e adicione as seguintes chaves:
   ```env
   OPENAI_API_KEY=your_openai_key
   FIRELIES_API_KEY=your_fireflies_key
   EMAIL_PASSWORD=your_email_password
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

3. **Conexão com o Supabase**:
   Configure o cliente Supabase com as variáveis `SUPABASE_URL` e `SUPABASE_KEY`.

## Uso

### Execução do Script Principal
1. **Processar transcritos**:
   O script faz uma requisição à API Fireflies para buscar transcritos das últimas reuniões.

2. **Gerenciar usuários e transcritos**:
   - Verifica no banco de dados se o usuário e os transcritos já existem.
   - Insere novos registros e associações.

3. **Análise de Objeções e Soft Skills**:
   Utiliza a API OpenAI para gerar relatórios de objeções e soft skills a partir das sentenças das reuniões.

4. **Envio de E-mails**:
   - Cria um relatório HTML detalhado com informações da reunião.
   - Envia o e-mail para os participantes da reunião usando Yagmail.

### Exemplo de Execução
Execute o script principal:
```bash
python main.py
```

## Funções Principais

### Carregar e Gerenciar Usuários
- **`carregar_usuarios()`**: Carrega todos os usuários existentes no banco de dados.
- **`obter_ou_criar_user_id(nome, user_cache)`**: Verifica ou insere um novo usuário no banco.

### Processamento de Transcritos
- **`process_transcripts_to_df(transcripts, user_cache)`**: Converte os transcritos em um DataFrame processado.
- **`verificar_e_inserir_transcripts(transcripts, user_cache)`**: Verifica e insere novos transcritos no banco de dados.
- **`inserir_sentences_em_lote(transcript_id, sentences, user_cache)`**: Insere as sentenças processadas no banco.

### Análise de Dados
- **`identificar_objeções(sentencas)`**: Identifica objeções levantadas nas transcrições.
- **`identificar_softskills(sentencas)`**: Analisa as soft skills utilizadas nas reuniões.

### Geração e Envio de Relatórios
- **`converter_negrito_para_html(texto)`**: Converte marcadores em negrito para tags HTML.
- **`gerar_message(row, objecoes, softskills)`**: Gera um relatório HTML com resumo e insights.
- **`send_mail(subject, message, emails)`**: Envia o e-mail com o relatório gerado.

## Estrutura do Projeto
```
project/
├── main.py              # Script principal
├── requirements.txt   # Dependências do projeto
├── .env               # Configurações de ambiente
├── README.md          # Documentação do projeto
```

## Melhoria Contínua
- **Automatização de testes**: Adicionar testes unitários para as principais funções.
- **Manutenção de logs**: Implementar logs para monitorar erros e sucessos.
- **Integração CI/CD**: Automatizar a implantação do projeto.

## Contribuições
Sinta-se à vontade para abrir issues ou enviar pull requests com melhorias ou correções.

## Licença
Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.

