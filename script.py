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
    limit: 1
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

# df = df[~df['id'].isin(ids_df['id'])]
# print('df filtrado', df.shape)


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




#%%
import yagmail

# Configuração
yag = yagmail.SMTP('admin@coachinvisivel.com', EMAIL_PASSWORD)

# Envio do e-mail


#%%
for _, row in df.iterrows():
    email_list = row['email'].split(',')
    email_list = [email.strip() for email in email_list]
    
    html_file = 'relatorio.html'
    with open(html_file, "w", encoding="utf-8") as arquivo:
        arquivo.write(row['message'])
    # Cria a lista final para 'to'
    # Converte HTML em PDF e salva no disco
    
    # Converte HTML para PDF
    
    # Envia o e-mail com o PDF anexado
    
    yag.send(
        to=['tiago.americano.03@gmail.com'],
        # to=['tiago.americano.03@gmail.com']+email_list,
        subject=f'Relatório Coach Invisível3 {row.date}',
        contents='Segue a baixo o relatório.',
        attachments=[html_file]  # Anexa o html gerado
    )
    
    print("E-mail enviado com sucesso!")


new_df = df[['id', 'names', 'email']]

# pd.concat([new_df, ids_df])[['id', 'names', 'email']].to_excel('ids.xlsx')
