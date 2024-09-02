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
    return build('admin', 'directory_v1', credentials=delegated_credentials)

def get_user_email_stats(service, user_email, retries=3):
    """Obtém estatísticas de e-mail para um usuário específico, com tentativas de repetição."""
    now = datetime.datetime.now()
    one_month_ago = (now - datetime.timedelta(days=30)).strftime("%Y/%m/%d")
    
    # Construir o serviço do Gmail usando as credenciais delegadas
    gmail_credentials = service._http.credentials.with_subject(user_email)
    gmail_service = build('gmail', 'v1', credentials=gmail_credentials)
    
    for attempt in range(retries):
        try:
            # Obter quantidade de e-mails enviados
            sent_results = gmail_service.users().messages().list(userId=user_email, q=f'from:{user_email} after:{one_month_ago}').execute()
            sent_count = len(sent_results.get('messages', []))
            
            # Obter quantidade de e-mails recebidos
            received_results = gmail_service.users().messages().list(userId=user_email, q=f'after:{one_month_ago}').execute()
            received_count = len(received_results.get('messages', []))

            # Obter quantidade de e-mails de spam
            spam_results = gmail_service.users().messages().list(userId=user_email, q=f'label:spam after:{one_month_ago}').execute()
            spam_count = len(spam_results.get('messages', []))

            return user_email, sent_count, received_count, spam_count
        
        except Exception as error:
            print(f"Ocorreu um erro para o usuário {user_email} na tentativa {attempt + 1}: {error}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return user_email, None, None, None

def get_all_users(service):
    """Recupera todos os usuários da API Directory."""
    users = []
    page_token = None
    
    while True:
        results = service.users().list(customer='my_customer', maxResults=100, pageToken=page_token, orderBy='email').execute()
        users.extend(results.get('users', []))
        page_token = results.get('nextPageToken')
        
        if not page_token:
            break
    
    return users

def main():
    print("Autenticando e recuperando usuários...")
    service = authenticate_directory_api()
    users = get_all_users(service)

    # Variáveis para armazenar os totais e máximos
    total_sent = 0
    total_received = 0
    total_spam = 0
    max_sent_email = ''
    max_sent_count = 0
    max_received_email = ''
    max_received_count = 0

    # Abrir o arquivo CSV para escrever os dados
    with open('gmail_api_stats.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Escrever o cabeçalho do CSV
        csvwriter.writerow(['User Email', 'Sent Emails', 'Received Emails', 'Spam Emails'])
        
        print("Coletando estatísticas de e-mail para cada usuário...")

        for user in users:
            user_email = user['primaryEmail']
            email_stats = get_user_email_stats(service, user_email)
            if email_stats[1] is not None and email_stats[2] is not None and email_stats[3] is not None:
                total_sent += email_stats[1]
                total_received += email_stats[2]
                total_spam += email_stats[3]
                
                if email_stats[1] > max_sent_count:
                    max_sent_email = user_email
                    max_sent_count = email_stats[1]
                if email_stats[2] > max_received_count:
                    max_received_email = user_email
                    max_received_count = email_stats[2]
                
                # Escrever as estatísticas de e-mail do usuário no CSV
                csvwriter.writerow(email_stats)

        # Escrever o resumo no final do arquivo CSV
        csvwriter.writerow([])
        csvwriter.writerow(['Summary'])
        csvwriter.writerow(['Metric', 'Value'])
        csvwriter.writerow(['Total Users', len(users)])
        csvwriter.writerow(['Total Sent Emails', total_sent])
        csvwriter.writerow(['Total Received Emails', total_received])
        csvwriter.writerow(['Total Spam Emails', total_spam])
        csvwriter.writerow(['Email with Most Sent Emails', max_sent_email])
        csvwriter.writerow(['Email with Most Received Emails', max_received_email])

    print("Processo concluído.")

if __name__ == '__main__':
    main()
