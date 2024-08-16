import requests
import csv
import datetime

# Defina as URLs da API e os tokens
glpi_url = "http://suporte.mirante.com.br/glpi/apirest.php"
app_token = "TZpa4UtZqdCKGVlVtT2OFtzCSvQJu9DkdpuvOejE"
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

# Função para buscar todos os chamados do último ano e contar por status
def get_chamados_ultimo_ano(session_token):
    headers["Session-Token"] = session_token
    now = datetime.datetime.now()
    one_year_ago = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    params = {
        "criteria[0][field]": "date",
        "criteria[0][searchtype]": "greaterthan",
        "criteria[0][value]": one_year_ago,  # Chamados criados no último ano
        "forcedisplay[0]": "2",  # ID do ticket
        "forcedisplay[1]": "12",  # Status do ticket
    }
    response = requests.get(f"{glpi_url}/Ticket", headers=headers, params=params)
    
    # Debug: exibir conteúdo da resposta
    print("Resposta da API:", response.json())

    if response.status_code == 200:
        tickets = response.json()
        
        # Verifique se a resposta está vazia
        if not tickets:
            print("Nenhum chamado encontrado no último ano.")
            return 0, {}
        
        # Contar chamados por status
        status_counts = {
            "Pendente": 0,
            "Fechado": 0,
            "Em Atendimento (Atribuído)": 0,
            "Aberto": 0,
            "Criado": 0,
            # Adicione outros status se necessário
        }
        for ticket in tickets:
            status = ticket["status"]
            if status == 2:  # Status 'Pendente'
                status_counts["Pendente"] += 1
            elif status == 6:  # Status 'Fechado'
                status_counts["Fechado"] += 1
            elif status == 4:  # Status 'Em Atendimento (Atribuído)'
                status_counts["Em Atendimento (Atribuído)"] += 1
            elif status == 1:  # Status 'Aberto'
                status_counts["Aberto"] += 1
            elif status == 0:  # Status 'Criado'
                status_counts["Criado"] += 1
        
        return len(tickets), status_counts
    else:
        raise Exception(f"Erro ao buscar chamados do último ano: {response.status_code} - {response.text}")

# Função para gerar o arquivo CSV
def generate_csv(qtd_criados, status_counts):
    with open('glpi_stats_summary.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Metric', 'Value'])
        csv_writer.writerow(['Quantidade Total de Chamados no Último Ano', qtd_criados])
        csv_writer.writerow(['Quantidade de Chamados Fechados', status_counts.get("Fechado", 0)])
        csv_writer.writerow(['Quantidade de Chamados Pendentes', status_counts.get("Pendente", 0)])
        csv_writer.writerow(['Quantidade de Chamados Em Atendimento (Atribuído)', status_counts.get("Em Atendimento (Atribuído)", 0)])
        csv_writer.writerow(['Quantidade de Chamados Abertos', status_counts.get("Aberto", 0)])
        csv_writer.writerow(['Quantidade de Chamados Criados', status_counts.get("Criado", 0)])

# Função principal
def main():
    try:
        session_token = init_session()
        
        qtd_criados, status_counts = get_chamados_ultimo_ano(session_token)
        
        generate_csv(qtd_criados, status_counts)
        print("Arquivo CSV 'glpi_stats_summary.csv' gerado com sucesso.")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
