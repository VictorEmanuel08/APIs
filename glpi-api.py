import requests
import csv
from datetime import datetime, timedelta

# Configurações da API
url_base = "http://189.17.228.135:3060/glpi/apirest.php"
app_token = "mIQnHEiuKLO7n6mCA0TprBSH0Dnhh1M6dPAtPYmL"
user_token = "geGLLICW6PQWnt9OxuW6ZxhcJL51hPRo5C3WDzKx"

# Cabeçalhos para iniciar a sessão
headers = {
    "App-Token": app_token,
    "Authorization": f"user_token {user_token}",
    "Content-Type": "application/json"
}

# Iniciar a sessão
init_session_endpoint = f"{url_base}/initSession"
response = requests.get(init_session_endpoint, headers=headers)

# Verificar se a sessão foi iniciada com sucesso
if response.status_code == 200:
    session_token = response.json().get('session_token')
    
    # Agora use o session_token para outras requisições
    headers['Session-Token'] = session_token
    
    # Calcula a data de 7 dias atrás
    seven_days_ago = datetime.now() - timedelta(days=7)
    seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')

    # Endpoint para listar os tickets com filtro por data
    endpoint = f"{url_base}/Ticket"
    
    # Parâmetros da requisição para filtrar tickets dos últimos 7 dias
    params = {
        "criteria[0][field]": "date_creation",
        "criteria[0][operator]": "greaterthan",
        "criteria[0][value]": seven_days_ago_str
    }
    
    # Fazendo a requisição
    response = requests.get(endpoint, headers=headers, params=params)
    
    # Verificando o status da resposta
    if response.status_code == 206 or response.status_code == 200:
        # Imprime a resposta completa para depuração
        print("Resposta da API:")
        tickets = response.json()
        print(tickets)  # Imprimir a resposta completa para verificar o formato
        
        # Filtrando tickets criados nos últimos 7 dias
        filtered_tickets = [ticket for ticket in tickets if datetime.strptime(ticket['date_creation'], '%Y-%m-%d %H:%M:%S') >= seven_days_ago]
        
        # Salvando as datas de criação e o total de tickets em um CSV
        with open('glpi_stats_summary.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Data de Criação'])
            for ticket in filtered_tickets:
                writer.writerow([ticket['id'], ticket['date_creation']])
            
            # Escreve o total de tickets no final do arquivo
            writer.writerow([])
            writer.writerow(['Total de Tickets nos últimos 7 dias', len(filtered_tickets)])
        
        print("Dados salvos em glpi_stats_summary.csv")
    else:
        print(f"Erro: {response.status_code} - {response.text}")
    
    # Encerrar a sessão quando terminar
    kill_session_endpoint = f"{url_base}/killSession"
    requests.get(kill_session_endpoint, headers=headers)

else:
    print(f"Erro ao iniciar sessão: {response.status_code} - {response.text}")
