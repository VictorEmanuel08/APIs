import requests
import csv

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
    
    # Endpoint para listar os tickets
    endpoint = f"{url_base}/Ticket"
    
    # Parâmetros da requisição
    params = {
        "range": "0-50"  # Ajuste o intervalo conforme necessário
    }
    
    # Fazendo a requisição
    response = requests.get(endpoint, headers=headers, params=params)
    
    # Verificando o status da resposta
    if response.status_code == 206 or response.status_code == 200:
        tickets = response.json()
        
        # Salvando os nomes e a quantidade total em um CSV
        with open('glpi_stats_summary.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'Nome'])
            for ticket in tickets:
                writer.writerow([ticket['id'], ticket['name']])
            
            # Escreve o total de tickets no final do arquivo
            writer.writerow([])
            writer.writerow(['Total de Tickets', len(tickets)])
        
        print("Dados salvos em glpi_stats_summary.csv")
    else:
        print(f"Erro: {response.status_code} - {response.text}")
    
    # Encerrar a sessão quando terminar
    kill_session_endpoint = f"{url_base}/killSession"
    requests.get(kill_session_endpoint, headers=headers)

else:
    print(f"Erro ao iniciar sessão: {response.status_code} - {response.text}")
