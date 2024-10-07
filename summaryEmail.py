import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

api_key_path = os.getenv('ANALYCTS_GMAIL_API_KEY_PATH')

SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly', 'https://www.googleapis.com/auth/gmail.readonly']
SERVICE_ACCOUNT_FILE = api_key_path
DELEGATED_ADMIN_EMAIL = 'victor.moura@mirante.com.br'

# Datas para os últimos 7 dias
end_date_last_7_days = datetime.today().strftime("%Y/%m/%d")
start_date_last_7_days = (datetime.today() - timedelta(days=7)).strftime("%Y/%m/%d")

# Datas para o mês atual
start_date_current_month = datetime.today().replace(day=1).strftime("%Y/%m/%d")
end_date_current_month = datetime.today().strftime("%Y/%m/%d")

# Datas para o mês anterior
first_day_of_current_month = datetime.today().replace(day=1)
last_day_previous_month = first_day_of_current_month - timedelta(days=1)
start_date_previous_month = last_day_previous_month.replace(day=1).strftime("%Y/%m/%d")
end_date_previous_month = last_day_previous_month.strftime("%Y/%m/%d")

def authenticate_directory_api():
    """Autentica e retorna o serviço da API Directory."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        delegated_credentials = credentials.with_subject(DELEGATED_ADMIN_EMAIL)
        return build('admin', 'directory_v1', credentials=delegated_credentials), credentials
    except Exception as e:
        print(f"Erro ao autenticar API Directory: {e}")
        return None, None
    
def get_sent_email_count(user_email, credentials, start_date, end_date):
    """Obtém a quantidade de e-mails enviados por um usuário em um intervalo de datas, lidando com paginação."""
    return get_email_count(user_email, credentials, start_date, end_date, 'from')

def get_received_email_count(user_email, credentials, start_date, end_date):
    """Obtém a quantidade de e-mails recebidos por um usuário em um intervalo de datas, lidando com paginação."""
    return get_email_count(user_email, credentials, start_date, end_date, 'to')

def get_email_count(user_email, credentials, start_date, end_date, email_direction):
    """Geral para obter a contagem de e-mails, baseado no critério de direção (from/to)."""
    try:
        gmail_credentials = credentials.with_subject(user_email)
        gmail_service = build('gmail', 'v1', credentials=gmail_credentials)

        query = f'{email_direction}:{user_email} after:{start_date} before:{end_date}'
        total_count = 0
        next_page_token = None

        while True:
            result = gmail_service.users().messages().list(
                userId=user_email, q=query, pageToken=next_page_token
            ).execute()

            total_count += len(result.get('messages', []))
            next_page_token = result.get('nextPageToken')

            if not next_page_token:
                break

        return total_count

    except Exception as error:
        print(f"Erro ao obter dados para {user_email}: {error}")
        return None

def get_email_stats_for_cft():
    # Autenticar e obter o serviço e credenciais
    service, credentials = authenticate_directory_api()
    
    if not credentials:
        print("Falha na autenticação. Verifique as credenciais e permissões.")
        return
    
    user_email = 'afonso.diniz@mirante.com.br'

    # Coletar os dados de e-mails enviados
    print(f"Obtendo e-mails enviados por {user_email} nos últimos 7 dias...")
    sent_last_7_days = get_sent_email_count(user_email, credentials, start_date_last_7_days, end_date_last_7_days)
    print(f"E-mails enviados nos últimos 7 dias: {sent_last_7_days}")

    print(f"Obtendo e-mails enviados por {user_email} no mês atual...")
    sent_current_month = get_sent_email_count(user_email, credentials, start_date_current_month, end_date_current_month)
    print(f"E-mails enviados no mês atual: {sent_current_month}")

    print(f"Obtendo e-mails enviados por {user_email} no mês anterior...")
    sent_previous_month = get_sent_email_count(user_email, credentials, start_date_previous_month, end_date_previous_month)
    print(f"E-mails enviados no mês anterior: {sent_previous_month}")

    # Coletar os dados de e-mails recebidos
    print(f"Obtendo e-mails recebidos por {user_email} nos últimos 7 dias...")
    received_last_7_days = get_received_email_count(user_email, credentials, start_date_last_7_days, end_date_last_7_days)
    print(f"E-mails recebidos nos últimos 7 dias: {received_last_7_days}")

    print(f"Obtendo e-mails recebidos por {user_email} no mês atual...")
    received_current_month = get_received_email_count(user_email, credentials, start_date_current_month, end_date_current_month)
    print(f"E-mails recebidos no mês atual: {received_current_month}")

    print(f"Obtendo e-mails recebidos por {user_email} no mês anterior...")
    received_previous_month = get_received_email_count(user_email, credentials, start_date_previous_month, end_date_previous_month)
    print(f"E-mails recebidos no mês anterior: {received_previous_month}")

    # Gerar o JSON com os resultados
    email_stats = {
        'email': user_email,
        'sent_last_7_days': sent_last_7_days,
        'sent_current_month': sent_current_month,
        'sent_previous_month': sent_previous_month,
        'received_last_7_days': received_last_7_days,
        'received_current_month': received_current_month,
        'received_previous_month': received_previous_month
    }

    # Salvar em cft.json
    json_output_path = os.path.join('json', 'cft.json')
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    
    with open(json_output_path, 'w') as json_file:
        json.dump(email_stats, json_file, indent=4)
    
    print(f"Estatísticas de e-mails salvas em {json_output_path}")

if __name__ == '__main__':
    get_email_stats_for_cft()
