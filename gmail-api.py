import concurrent.futures
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import csv
import time

# Definir os escopos e o arquivo da conta de serviço
SCOPES = ['https://www.googleapis.com/auth/admin.directory.user.readonly', 'https://www.googleapis.com/auth/gmail.readonly']
SERVICE_ACCOUNT_FILE = 'analycts-gmail-api-f45bf723f256.json'
DELEGATED_ADMIN_EMAIL = 'victor.moura@mirante.com.br'

def authenticate_directory_api():
    """Autentica e retorna o serviço da API Directory."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_credentials = credentials.with_subject(DELEGATED_ADMIN_EMAIL)
    return build('admin', 'directory_v1', credentials=delegated_credentials), credentials

def get_user_email_stats(user_email, credentials):
    """Obtém estatísticas de e-mail para um usuário específico."""
    now = datetime.datetime.now()
    one_week_ago = (now - datetime.timedelta(days=7)).strftime("%Y/%m/%d")

    try:
        gmail_credentials = credentials.with_subject(user_email)
        gmail_service = build('gmail', 'v1', credentials=gmail_credentials)
        
        # Obter a quantidade de e-mails enviados, recebidos, spam e não lidos
        queries = {
            'sent': f'from:{user_email} after:{one_week_ago}',
            'received': f'after:{one_week_ago}',
            'spam': f'label:spam after:{one_week_ago}',
            'unread': 'is:unread'
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

def main():
    start_time = time.time()
    print("Autenticando e recuperando usuários...")
    service, credentials = authenticate_directory_api()
    users = get_all_users(service)

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

    print("Coletando estatísticas de e-mail para cada usuário...")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(get_user_email_stats, user['primaryEmail'], credentials): user for user in users}
        for future in concurrent.futures.as_completed(futures):
            user_email, sent_count, received_count, spam_count, unread_count = future.result()
            
            user_status = futures[future].get('suspended', False)
            if user_status:
                suspended_users += 1
            else:
                active_users += 1

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

    with open('email_stats_summary.csv', 'w', newline='') as summary_file:
        summary_writer = csv.writer(summary_file)
        summary_writer.writerow(['Metric', 'Value'])
        summary_writer.writerow(['Total Sent Emails', total_sent])
        summary_writer.writerow(['Total Received Emails', total_received])
        summary_writer.writerow(['Total Spam Emails', total_spam])
        summary_writer.writerow(['Total Unread Emails', total_unread])
        summary_writer.writerow(['Email with Most Sent Emails', max_sent_email])
        summary_writer.writerow(['Email with Most Received Emails', max_received_email])
        summary_writer.writerow(['Number of Users', len(users)])
        summary_writer.writerow(['Number of Active Users', active_users])
        summary_writer.writerow(['Number of Suspended Users', suspended_users])

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Processo concluído em {execution_time:.2f} segundos.")

if __name__ == '__main__':
    main()
