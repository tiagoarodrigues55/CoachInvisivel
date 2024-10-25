import requests
import json
from datetime import datetime, timedelta, timezone
import pandas as pd
from openai import OpenAI

import os

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
API_KEY = os.getenv("FIRELIES_API_KEY")
print('API_KEY carregado', API_KEY)
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

client = OpenAI(api_key=OPENAI_KEY)

# Configure sua API key da OpenAI
client = OpenAI(api_key=OPENAI_KEY)

# Replace with your actual API endpoint and authentication
API_ENDPOINT = "https://api.fireflies.ai/graphql"

# GraphQL query
query = """
query LastTenTranscripts {
  transcripts(
    limit: 10
    skip: 0
  ) {
     id
 speakers{name}
      date
      dateString
    summary {
      gist
      action_items
      overview
      bullet_gist
      shorthand_bullet
    }
    sentences {
      text
      speaker_name
}

  }
}
"""

# Calculate date range (last 30 days)
to_date = datetime.utcnow()
from_date = to_date - timedelta(days=7)

# Format dates for the query
variables = {
    "fromDate": from_date.isoformat() + "Z",
    "toDate": to_date.isoformat() + "Z"
}

# Set up the request
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Make the request
response = requests.post(
    API_ENDPOINT,
    headers=headers,
    json={"query": query}
)

# Check if the request was successful
data = response.json()
transcripts = data.get("data", {}).get("transcripts", [])
print('transcripts carregados', len(transcripts))

def converter_timestamp_para_data_brasilia(timestamp):
    # Define o fuso horário de Brasília (UTC-3)
    fuso_horario_brasilia = timezone(timedelta(hours=-3))

    # Converte o timestamp para um objeto datetime no fuso UTC
    data_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)

    # Ajusta para o horário de Brasília
    data_brasilia = data_utc.astimezone(fuso_horario_brasilia)

    # Formata a data no formato desejado: dd/mm/aaaa
    data_formatada = data_brasilia.strftime('%d/%m/%Y')
    
    return data_formatada

# Exemplo de uso

def process_transcripts_to_df(transcripts, users_df):
    processed_data = []

    for transcript in transcripts:
        if type(transcript['speakers']) != list:
            continue

        # Extrai nomes dos speakers
        speaker_names = [speaker["name"] for speaker in transcript["speakers"]]
        names = ", ".join(speaker_names)

        # Converte a data
        date = pd.to_datetime(transcript["dateString"]).strftime('%d/%m/%Y')

        summary = transcript["summary"]
        sentences = json.dumps(transcript["sentences"], ensure_ascii=False)

        # Encontra emails correspondentes aos nomes no users_df
        matching_emails = users_df[users_df['nome'].isin(speaker_names)]['email'].tolist()
        email = ", ".join(matching_emails) if matching_emails else None

        # Cria um dicionário com as informações necessárias
        row = {"names": names, "date": date, "email": email, "sentences": sentences, **summary, "id": transcript['id']}
        processed_data.append(row)

    # Cria o DataFrame a partir da lista de dicionários
    df = pd.DataFrame(processed_data)
    return df


# Gerando o DataFrame
ids_df = pd.read_excel('ids.xlsx')
print('ids_df carregado', ids_df.shape)

users_df = pd.read_excel('users.xlsx')
print('users_df carregado', users_df.shape)

df = process_transcripts_to_df(transcripts, users_df)
print('df carregado', df.shape)

df = df[~df['id'].isin(ids_df['id'])]
print('df filtrado', df.shape)


df.to_excel('transcripts.xlsx')


if len(df['id']) == 0:
    exit()
#%%




def identificar_objeções(sentencas):
    # Formata o prompt com as sentenças fornecidas
    prompt = (
        "Analise as seguintes sentenças e identifique as principais objeções levantadas na conversa.\n\n"
        + sentencas +
        "\n\nQuais são as principais objeções discutidas na conversa? Me retorne apenas uma lista com as objeções"
    )
    # Chamada para a API da OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    # Retorna a resposta da API

    return completion.choices[0].message.content.replace('```', '').replace('html', '')  # Acessando o conteúdo corretamente

df['objecoes'] = df['sentences'].apply(identificar_objeções)

#%%

# def analisar_topicos(sentencas):
#     # Formata o prompt com as sentenças fornecidas
#     prompt = (
#         """"Você irá atuar como um analista de transcrições de reuniões de vendas, avaliando as falas dos participantes com base em cinco dimensões fundamentais extraídas do livro 'The Salesperson’s Secret Code'. As dimensões são:

#         Fulfilment (Realização): Demonstrar satisfação com o progresso ou metas alcançadas. Busque frases que indiquem ambição ou busca por excelência pessoal.
#         Control (Controle): Identificar planejamento e senso de responsabilidade. Veja se os participantes assumem responsabilidade pelos resultados, mencionam planos claros, ou evitam atribuir culpa a fatores externos.
#         Resilience (Resiliência): Procure sinais de capacidade de superar obstáculos e adaptação a desafios. Busque exemplos de perseverança após contratempos.
#         Influence (Influência): Avalie se os participantes conseguem influenciar outras pessoas, seja dentro da equipe ou com clientes, e se mostram capacidade de construir redes de apoio.
#         Communication (Comunicação): Observe a clareza, objetividade e eficácia na comunicação. Identifique quando a comunicação gera engajamento e promove colaboração.
#         Você deverá:

#         Destacar trechos relacionados a cada dimensão.
#         Oferecer uma análise breve sobre como cada dimensão foi demonstrada ou ausente.
#         Fornecer recomendações para melhorar em cada dimensão, se necessário.
#                 \n\n"""
#         + sentencas
#     )
#     # Chamada para a API da OpenAI
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}]
#     )

#     # Retorna a resposta da API

#     return completion.choices[0].message.content.replace('```', '').replace('html', '')  # Acessando o conteúdo corretamente

# df['topicos'] = df['sentences'].apply(analisar_topicos)




#%%

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuração da conta do Outlook
EMAIL = "assistente@coachinvisivel.com"
PASSWORD = "Leadera@2024*"
SMTP_SERVER = "mail.coachinvisivel.com"  # Altere para o servidor SMTP do HostGator
SMTP_PORT = 587  # A porta 587 é geralmente usada para SMTP com TLS



# Função para enviar e-mails
def enviar_email(row):
    destinatario = 'tiago.americano.03@gmail.com'
    assunto = f"Relatório Coach Invisível {row['date']}"

    # Configurando o e-mail em HTML
    html_body = f"""
    <html>
    <body>
        <h2>Resumo Principal</h2>
        <p>{row['gist']}</p>

        <h3>Principais pontos</h3>
        <pre>{row['bullet_gist']}</pre>

        <h3>Itens de Ação</h3>
        <pre>{row['action_items']}</pre>

        <h3>Visão Geral</h3>
        <p>{row['overview']}</p>
        
        <h3>Objeções</h3>
        <p>{row['objecoes']}</p>
        
        <h3>Próximos passos</h3>
        <p>{row['shorthand_bullet']}</p>
    </body>
    </html>
    """       
    
    print(html_body)

    # Criando a mensagem MIME
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = destinatario
    # msg['Cc'] =  row['email']
    msg['Subject'] = assunto
    msg.attach(MIMEText(html_body, 'html'))

    # Enviando o e-mail via SMTP
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Inicia a comunicação segura
            server.login(EMAIL, PASSWORD)  # Login na conta
            server.sendmail(EMAIL, destinatario, msg.as_string())
        print(f"E-mail enviado para {destinatario}!")
    except Exception as e:
        print(f"Erro ao enviar e-mail para {destinatario}: {e}")




#%%
import pywhatkit

def send_msg(message, number = "+5511992481655"):
    now = datetime.now()
    hour = now.hour
    minute = now.minute + 1
    print(number, message, hour, minute, 15, True, 5)
    pywhatkit.sendwhatmsg(number, message, hour, minute, 15, True, 5)

#%%

import re

def converter_negrito_para_html(texto):
    # Expressão regular para encontrar o padrão **texto**
    texto_convertido = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
    return texto_convertido


def gerar_message(row):
    # Gera o HTML com os valores de cada linha.
    message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
            <div style="background-color: #ffffff; padding: 20px; border-radius: 8px; 
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); max-width: 600px; margin: auto;">
                
                <h3 style="color: #333; border-bottom: 2px solid #f0ad4e; padding-bottom: 5px;">
                    Resumo Principal
                </h3>
                <p style="color: #555; line-height: 1.6; margin-bottom: 15px;">
                    {converter_negrito_para_html(row['gist'])}
                </p>
    
                <h3 style="color: #333; border-bottom: 2px solid #f0ad4e; padding-bottom: 5px;">
                    Principais pontos
                </h3>
                <pre style="color: #555; line-height: 1.6; margin-bottom: 15px; 
                            background-color: #f7f7f7; padding: 10px; border-radius: 5px; 
                            overflow-x: auto; white-space: pre-wrap;">
{converter_negrito_para_html(row['bullet_gist'])}
                </pre>
    
                <h3 style="color: #333; border-bottom: 2px solid #f0ad4e; padding-bottom: 5px;">
                    Itens de Ação
                </h3>
                <pre style="color: #555; line-height: 1.6; margin-bottom: 15px; 
                            background-color: #f7f7f7; padding: 10px; border-radius: 5px; 
                            overflow-x: auto; white-space: pre-wrap;">
{converter_negrito_para_html(row['action_items'])}
                </pre>
    
                <h3 style="color: #333; border-bottom: 2px solid #f0ad4e; padding-bottom: 5px;">
                    Visão Geral
                </h3>
                <p style="color: #555; line-height: 1.6; margin-bottom: 15px;">
                    {converter_negrito_para_html(row['overview'])}
                </p>
    
                <h3 style="color: #333; border-bottom: 2px solid #f0ad4e; padding-bottom: 5px;">
                    Objeções
                </h3>
                <pre style="color: #555; line-height: 1.6; margin-bottom: 15px; 
                            background-color: #f7f7f7; padding: 10px; border-radius: 5px; 
                            overflow-x: auto; white-space: pre-wrap;">
{converter_negrito_para_html(row['objecoes'])}
                </pre>
    
                <h3 style="color: #333; border-bottom: 2px solid #f0ad4e; padding-bottom: 5px;">
                    Próximos passos
                </h3>
                <pre style="color: #555; line-height: 1.6; margin-bottom: 15px; 
                            background-color: #f7f7f7; padding: 10px; border-radius: 5px; 
                            overflow-x: auto; white-space: pre-wrap;">
{converter_negrito_para_html(row['shorthand_bullet'])}
                </pre>
                

            </div>
        </body>
    </html>
    """

    print(message)    
    return message

df['message'] = df.apply(gerar_message, axis=1)

# Cria a nova coluna 'message' aplicando a função `gerar_html` em cada linha do DataFrame.


#%%

# def formatar_html(html):
#     # Formata o prompt com as sentenças fornecidas
#     prompt = (
#         "Formate meu html de forma que as informações fiquem estruturadas como um email profissional: \n\n"
#         + html + "Me retorne apenas um código html como resposta."
#     )
#     # Chamada para a API da OpenAI
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}]
#     )

#     # Retorna a resposta da API

#     return completion.choices[0].message.content.replace('```', '').replace('html', '')  # Acessando o conteúdo corretamente

# df['html'] = df['message'].apply(identificar_objeções)



#%%
import yagmail

# Configuração
yag = yagmail.SMTP('admin@coachinvisivel.com', EMAIL_PASSWORD)

# Envio do e-mail


#%%
for _, row in df.iterrows():
    email_list = row['email'].split(',')
    email_list = [email.strip() for email in email_list]
    
    # Cria a lista final para 'to'
    yag.send(
        # to=['tiago.americano.03@gmail.com'],
        to=['tiago.americano.03@gmail.com']+email_list,
        
        subject=f'Relatório Coach Invisível {row.date}',
        contents=row['message']
    )
    print('E-mail enviado com sucesso!')
    # send_msg(row['message'])

new_df = df[['id', 'names', 'email']]

pd.concat([new_df, ids_df])[['id', 'names', 'email']].to_excel('ids.xlsx')
