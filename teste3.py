import requests
import json

#Novo teste
# Configurações da API GLPI
base_url = "http://suporte.mirante.com.br/glpi/apirest.php"
app_token = "mIQnHEiuKLO7n6mCA0TprBSH0Dnhh1M6dPAtPYmL"
user_token = "3VyFes6s71d4JrrMvwXNdQ7XX4Inl79UG1pLnId4"

# Função para iniciar sessão
def init_session():
    url = f"{base_url}/initSession"
    headers = {
        'App-Token': app_token,
        'Authorization': f'user_token {user_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        session_token = response.json().get('session_token')
        print(f"Sessão iniciada com sucesso. Session Token: {session_token}")
        return session_token
    else:
        print(f"Erro ao iniciar sessão: {response.status_code} - {response.text}")
        return None

# Função para buscar os últimos 10 chamados solucionados
def get_solved_tickets(session_token):
    url = f"{base_url}/search/Ticket"
    headers = {
        'App-Token': app_token,
        'Session-Token': session_token,
        'Content-Type': 'application/json'
    }

    # Ajustando a requisição para buscar chamados solucionados
    params = {
        'criteria[0][field]': '12',  # Campo status
        'criteria[0][searchtype]': 'equals',
        'criteria[0][value]': '2',  # Valor para status 
        'criteria[1][field]': '15',  # Campo data de abertura
        'criteria[1][searchtype]': 'morethan',  # para valores maior que a data informada
        'criteria[1][value]': '2024-08-22 00:00:00',  # Data inicio
        'sort': '15',  # Ordenar por data de abertura
        'order': 'ASC',  # Ordem decrescente
        #'range': '0-2',  # Limitar a 3 resultados
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code in [200, 206]:
        # Imprimir o JSON completo da resposta para análise
        print("Resposta completa da API:")
        print(json.dumps(response.json(), indent=4))
        
        tickets = response.json().get('data', [])
        if tickets:
            print("Últimos 10 chamados solucionados:")
            for ticket in tickets:
                ticket_id = ticket.get("2", 'ID não encontrado')
                ticket_name = ticket.get('1', 'Nome não encontrado')
                ticket_open = ticket.get('15', 'Data de abertura não encontrada')
                print(f"ID: {ticket_id} - Título: {ticket_name} - Data de abertura {ticket_open}")
        else:
            print("Nenhum chamado solucionado encontrado.")
    else:
        print(f"Erro ao buscar chamados: {response.status_code} - {response.text}")

# Função para encerrar sessão
def kill_session(session_token):
    url = f"{base_url}/killSession"
    headers = {
        'App-Token': app_token,
        'Session-Token': session_token,
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        print("Sessão encerrada com sucesso.")
    else:
        print(f"Erro ao encerrar sessão: {response.status_code} - {response.text}")

# Execução do programa
if __name__ == "__main__":
    session_token = init_session()
    if session_token:
        get_solved_tickets(session_token)
        kill_session(session_token)
    else:
        print("Não foi possível iniciar a sessão. Verifique os tokens e tente novamente.")
