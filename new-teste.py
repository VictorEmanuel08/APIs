import requests

# Defina as URLs da API e os tokens
glpi_url = "http://suporte.mirante.com.br/glpi/apirest.php"
app_token = "mIQnHEiuKLO7n6mCA0TprBSH0Dnhh1M6dPAtPYmL"
user_token = "geGLLICW6PQWnt9OxuW6ZxhcJL51hPRo5C3WDzKx"

# Cabeçalhos de autenticação
headers = {
    "App-Token": app_token,
    "Authorization": f"user_token {user_token}",
    "Content-Type": "application/json"
}

# Função para iniciar a sessão na API
def init_session():
    response = requests.get(f"{glpi_url}/initSession", headers=headers)
    if response.status_code == 200:
        return response.json()["session_token"]
    else:
        raise Exception(f"Erro ao iniciar a sessão: {response.status_code} - {response.text}")

# Função para buscar todos os chamados e contar o total
def get_total_tickets(session_token):
    headers["Session-Token"] = session_token
    total_tickets = 0
    page = 0
    while True:
        params = {
            "start": page * 100,  # Defina o início da página
            "limit": 100          # Defina o tamanho da página
        }
        response = requests.get(f"{glpi_url}/Ticket", headers=headers, params=params)
        if response.status_code in [200, 206]:
            tickets = response.json()
            if not tickets:  # Se a resposta estiver vazia, pare a iteração
                break
            total_tickets += len(tickets)
            page += 1
        else:
            raise Exception(f"Erro ao buscar chamados: {response.status_code} - {response.text}")
    return total_tickets

# Função principal
def main():
    try:
        session_token = init_session()
        total_tickets = get_total_tickets(session_token)
        print(f"Quantidade total de chamados: {total_tickets}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
