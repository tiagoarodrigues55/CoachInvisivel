import requests
import json
from datetime import datetime, timedelta, timezone
import pandas as pd
from openai import OpenAI
import yagmail
import os
from supabase import create_client, Client
import ast
import time
# Configuração



OPENAI_KEY = os.getenv("OPENAI_API_KEY")
API_KEY = os.getenv("FIRELIES_API_KEY")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# Configurar o cliente Supabase

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Configuração
yag = yagmail.SMTP('admin@coachinvisivel.com', EMAIL_PASSWORD)

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

# Carrega todos os usuários existentes para evitar múltiplas consultas repetidas
def carregar_usuarios():
    """Carrega todos os usuários e retorna um dicionário {nome: user_id}."""
    users = supabase.table("users").select("id, name").execute().data
    user_cache = {}
    for user in users:
        for name in user["name"]:
            user_cache[name] = user["id"]
    return user_cache

# Cria ou retorna o ID de um usuário usando o cache
def obter_ou_criar_user_id(nome, user_cache):
    """Verifica no cache ou insere o usuário no banco, atualizando o cache."""
    if nome in user_cache:
        return user_cache[nome]

    # Se não encontrado no cache, insere o novo usuário
    response = supabase.table("users").insert({"name": [nome]}).execute()
    novo_user_id = response.data[0]["id"]

    # Atualiza o cache com o novo usuário
    user_cache[nome] = novo_user_id
    return novo_user_id

def process_transcripts_to_df(transcripts, user_cache):
    """Processa os transcripts e extrai os dados necessários."""
    processed_data = []

    for transcript in transcripts:
        if not isinstance(transcript["speakers"], list):
            continue

        # Usa o cache para obter ou criar IDs de usuários
        speaker_ids = [obter_ou_criar_user_id(speaker["name"], user_cache) for speaker in transcript["speakers"]]

        meet_date = pd.to_datetime(transcript["dateString"], utc=True).isoformat()

        summary = transcript.get("summary", {})
        row = {
            "fireflies_id": transcript["id"],
            "meet_date": meet_date,
            "gist": summary.get("gist"),
            "action_items": summary.get("action_items"),
            "overview": summary.get("overview"),
            "bullet_gist": summary.get("bullet_gist"),
            "shorthand_bullet": summary.get("shorthand_bullet"),
            "speakers": speaker_ids,
            "sentences": transcript["sentences"]
        }
        processed_data.append(row)

    return pd.DataFrame(processed_data)

def inserir_sentences_em_lote(transcript_id, sentences, user_cache):
    """Prepara e insere sentences em lote."""
    batch_data = []

    for sentence in sentences:
        ai_filters = sentence.get("ai_filters", {})
        speaker_name = sentence.get("speaker_name")
        user_id = obter_ou_criar_user_id(speaker_name, user_cache)

        # Monta a sentence em formato de dicionário
        batch_data.append({
            "transcript_id": transcript_id,
            "user_id": user_id,
            "start_time": sentence.get("start_time"),
            "end_time": sentence.get("end_time"),
            "text": sentence.get("text"),
            "sentiment": ai_filters.get("sentiment"),
            "question": ai_filters.get("question"),
            "task": ai_filters.get("task")
        })
        
    print('sentences preparadas para inserção em massa')

    # Realiza a inserção em lote
    if batch_data:
        supabase.table("sentences").insert(batch_data).execute()

def verificar_e_inserir_transcripts(transcripts, user_cache):
    """Verifica e insere novos transcripts e suas sentences no banco."""
    ids_existentes = supabase.table("transcripts").select("fireflies_id").execute().data
    ids_existentes = {item["fireflies_id"] for item in ids_existentes}

    novos_transcripts = [t for t in transcripts if t["id"] not in ids_existentes]
    if novos_transcripts:
        df = process_transcripts_to_df(novos_transcripts, user_cache)
        ids = []
        for _, row in df.iterrows():
            transcript_response = supabase.table("transcripts").insert({
                "fireflies_id": row["fireflies_id"],
                "meet_date": row["meet_date"],
                "gist": row["gist"],
                "action_items": row["action_items"],
                "overview": row["overview"],
                "bullet_gist": row["bullet_gist"],
                "shorthand_bullet": row["shorthand_bullet"],
                "speakers": row["speakers"]
            }).execute()

            transcript_id = transcript_response.data[0]["id"]
            ids.append(transcript_id)
            
            print('inserindo sentences...')

            # Inserir todas as sentences em lote
            inserir_sentences_em_lote(transcript_id, row["sentences"], user_cache)

        print(f"{len(novos_transcripts)} novos transcripts inseridos.")
        return ids

    else:
        print("Nenhum novo transcript para inserir.")
        return []
# Carrega o cache de usuários
user_cache = carregar_usuarios()


# Executa a verificação e inserção
novos_ids = verificar_e_inserir_transcripts(transcripts, user_cache)
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






#%%

import re

def converter_negrito_para_html(texto):
    # Expressão regular para encontrar o padrão **texto**
    texto_convertido = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
    return texto_convertido


def gerar_message(row, objecoes):
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
{converter_negrito_para_html(objecoes)}
                </pre>
                    
            </div>
        </body>
    </html>
    """

    return message




def send_mail(subject, message, emails):
    html_file = 'relatorio.html'
    with open(html_file, "w", encoding="utf-8") as arquivo:
        arquivo.write(message)
    
    yag.send(
        to=['pedro.ferrufino@greatpeople.com'],
        # to=['tiago.americano.03@gmail.com']+emails,

        subject=subject,
        contents='Segue o relatório',
        attachments=[html_file]  # Anexa o PDF gerado
    )

novos_ids = [15, 17, 19, 18, 20, 21]

for id in novos_ids:
    sentences = supabase.table("sentences").select("*").eq("transcript_id", id).execute().data
    transcript = supabase.table("transcripts").select("*").eq("id", id).execute().data[0]

    
    subject = f"Relatório Coach Invisível {datetime.fromisoformat(transcript['meet_date']).strftime('%d/%m/%Y')}"
    
    response = (
        supabase.table("user_assistants_view")
        .select("*")
        .in_("user_id", transcript['speakers'])
        .execute()
    )
    emails_unicos = set()  # Conjunto para evitar e-mails duplicados
    
    for user in response.data:
        emails = user.get("user_email", [])

        if emails:  # Verifica se há e-mails e não é uma lista vazia
            emails_unicos.update(emails)
    
    # Converte o conjunto de e-mails para lista
    emails_final = list(emails_unicos)
    

    objecoes = identificar_objeções(str([sentence["text"] for sentence in sentences if "text" in sentence]))
    
    message = gerar_message(transcript, objecoes)
        
    send_mail(subject, message, emails_final)