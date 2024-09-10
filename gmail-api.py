import concurrent.futures
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import csv
import time
from dotenv import load_dotenv
import os

load_dotenv()

api_key_path = os.getenv('ANALYCTS_GMAIL_API_KEY_PATH')

SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly', 'https://www.googleapis.com/auth/gmail.readonly']
SERVICE_ACCOUNT_FILE = api_key_path
DELEGATED_ADMIN_EMAIL = 'victor.moura@mirante.com.br'

# Criar a pasta "gmail-api" se não existir
output_folder = 'gmail-api'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def authenticate_directory_api():
    """Autentica e retorna o serviço da API Directory."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_credentials = credentials.with_subject(DELEGATED_ADMIN_EMAIL)
    return build('admin', 'directory_v1', credentials=delegated_credentials), credentials

def get_user_email_stats(user_email, credentials, start_date, end_date):
    """Obtém estatísticas de e-mail para um usuário específico dentro de um intervalo de datas."""
    try:
        gmail_credentials = credentials.with_subject(user_email)
        gmail_service = build('gmail', 'v1', credentials=gmail_credentials)
        
        # Obter a quantidade de e-mails enviados, recebidos, spam e não lidos
        queries = {
            'sent': f'from:{user_email} after:{start_date} before:{end_date}',
            'received': f'after:{start_date} before:{end_date}',
            'spam': f'label:spam after:{start_date} before:{end_date}',
            'unread': f'is:unread after:{start_date} before:{end_date}'
        }
        
        results = {}
        for label, query in queries.items():
            result = gmail_service.users().messages().list(userId=user_email, q=query).execute()
            results[label] = len(result.get('messages', []))

        return user_email, results['sent'], results['received'], results['spam'], results['unread']

    except Exception as error:
        print(f"Erro para o usuário {user_email}: {error}")
        return user_email, None, None, None, None

def get_all_users(service):
    """Recupera todos os usuários da API Directory."""
    users = []
    page_token = None
    
    while True:
        results = service.users().list(customer='my_customer', maxResults=500, pageToken=page_token, orderBy='email').execute()
        users.extend(results.get('users', []))
        page_token = results.get('nextPageToken')
        
        if not page_token:
            break
    
    return users

def generate_monthly_reports(users, service, credentials, year):
    """Gera relatórios mensais de e-mail para cada mês do ano até o mês atual, ignorando os já gerados."""
    current_month = datetime.datetime.now().month
    for month in range(1, current_month + 1):
        output_file = os.path.join(output_folder, f'{year}-{month:02d}.csv')
        
        # Ignorar o arquivo se ele já existe e não é o mês atual
        if os.path.exists(output_file) and month != current_month:
            print(f"Relatório para {year}-{month:02d} já existe. Ignorando...")
            continue
        
        start_date = datetime.date(year, month, 1).strftime("%Y/%m/%d")
        end_date = (datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)).strftime("%Y/%m/%d")

        total_sent = 0
        total_received = 0
        total_spam = 0
        total_unread = 0
        max_sent_email = ''
        max_sent_count = 0
        max_received_email = ''
        max_received_count = 0

        print(f"Coletando estatísticas para {year}-{month:02d}...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(get_user_email_stats, user['primaryEmail'], credentials, start_date, end_date): user for user in users}
            for future in concurrent.futures.as_completed(futures):
                user_email, sent_count, received_count, spam_count, unread_count = future.result()

                if sent_count is not None and received_count is not None:
                    total_sent += sent_count
                    total_received += received_count
                    total_spam += spam_count
                    total_unread += unread_count

                    if sent_count > max_sent_count:
                        max_sent_email = user_email
                        max_sent_count = sent_count
                    if received_count > max_received_count:
                        max_received_email = user_email
                        max_received_count = received_count

        # Escrever os dados no arquivo CSV
        with open(output_file, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Metric', 'Value'])
            csv_writer.writerow(['Total Sent Emails', total_sent])
            csv_writer.writerow(['Total Received Emails', total_received])
            csv_writer.writerow(['Total Spam Emails', total_spam])
            csv_writer.writerow(['Total Unread Emails', total_unread])
            csv_writer.writerow(['Email with Most Sent Emails', max_sent_email])
            csv_writer.writerow(['Email with Most Received Emails', max_received_email])

def generate_last_7_days_summary(users, credentials):
    """Gera um resumo dos últimos 7 dias e salva em last_7_days_summary.csv."""
    end_date = datetime.date.today().strftime("%Y/%m/%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y/%m/%d")

    total_sent = 0
    total_received = 0
    total_spam = 0
    total_unread = 0
    max_sent_email = ''
    max_sent_count = 0
    max_received_email = ''
    max_received_count = 0
    active_users = 0
    suspended_users = 0

    print("Coletando estatísticas para os últimos 7 dias...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(get_user_email_stats, user['primaryEmail'], credentials, start_date, end_date): user for user in users}
        for future in concurrent.futures.as_completed(futures):
            user_email, sent_count, received_count, spam_count, unread_count = future.result()

            if sent_count is not None and received_count is not None:
                total_sent += sent_count
                total_received += received_count
                total_spam += spam_count
                total_unread += unread_count

                if sent_count > max_sent_count:
                    max_sent_email = user_email
                    max_sent_count = sent_count
                if received_count > max_received_count:
                    max_received_email = user_email
                    max_received_count = received_count

    # Contar usuários ativos e suspensos
    for user in users:
        if user.get('suspended', False):
            suspended_users += 1
        else:
            active_users += 1

    # Escrever os dados no arquivo last_7_days_summary.csv
    summary_file = os.path.join(output_folder, 'last_7_days_summary.csv')
    with open(summary_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Metric', 'Value'])
        csv_writer.writerow(['Total Sent Emails', total_sent])
        csv_writer.writerow(['Total Received Emails', total_received])
        csv_writer.writerow(['Total Spam Emails', total_spam])
        csv_writer.writerow(['Total Unread Emails', total_unread])
        csv_writer.writerow(['Email with Most Sent Emails', max_sent_email])
        csv_writer.writerow(['Email with Most Received Emails', max_received_email])
        csv_writer.writerow(['Number of Users', len(users)])
        csv_writer.writerow(['Number of Active Users', active_users])
        csv_writer.writerow(['Number of Suspended Users', suspended_users])

def main():
    start_time = time.time()
    print("Autenticando e recuperando usuários...")
    service, credentials = authenticate_directory_api()
    users = get_all_users(service)

    print("Gerando relatórios mensais...")
    generate_monthly_reports(users, service, credentials, datetime.datetime.now().year)

    print("Gerando resumo dos últimos 7 dias...")
    generate_last_7_days_summary(users, credentials)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Processo concluído em {execution_time:.2f} segundos.")

if __name__ == '__main__':
    main()
