import requests
import csv
from datetime import datetime, timedelta
import os

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

# Função para buscar todos os chamados criados nos últimos 7 dias
def get_all_recent_tickets(session_token):
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    
    url = f"{base_url}/search/Ticket"
    headers = {
        'App-Token': app_token,
        'Session-Token': session_token,
        'Content-Type': 'application/json'
    }

    params = {
        'criteria[0][field]': '15',  # Campo data de abertura
        'criteria[0][searchtype]': 'morethan',  # para valores maior que a data informada
        'criteria[0][value]': seven_days_ago,  # Data de 7 dias atrás
        'sort': '15',  # Ordenar por data de abertura
        'order': 'DESC',  # Ordem decrescente
        'forcedisplay[0]': '2',  # ID do ticket
        'forcedisplay[1]': '1',  # Título do ticket
        'forcedisplay[2]': '12',  # Status do ticket
        'forcedisplay[3]': '15',  # Data de abertura do ticket
        'range': '0-999999'  # Tentar obter todos os tickets
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code in [200, 206]:
        tickets = response.json().get('data', [])
        return tickets
    else:
        print(f"Erro ao buscar chamados: {response.status_code} - {response.text}")
        return []

# Função para salvar dados em CSV
def save_data_to_files(tickets):
    # Criar a pasta 'glpi-api' se não existir
    output_dir = 'glpi-api'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Remover IDs e criar lista de tickets sem ID
    filtered_tickets = []
    status_count = {}

    for ticket in tickets:
        ticket_info = {
            'Title': ticket.get('1', 'Nome não encontrado'),
            'Status': ticket.get('12', 'Status não encontrado'),
            'Open Date': ticket.get('15', 'Data de abertura não encontrada')
        }
        filtered_tickets.append(ticket_info)

        # Contagem por status
        status = ticket_info['Status']
        if status in status_count:
            status_count[status] += 1
        else:
            status_count[status] = 1

    # Caminho dos arquivos CSV
    summary_file = os.path.join(output_dir, 'glpi_stats_summary.csv')
    status_summary_file = os.path.join(output_dir, 'glpi_stats_status_summary.csv')

    # Salvar tickets em CSV
    with open(summary_file, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['Title', 'Status', 'Open Date']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(filtered_tickets)

    # Salvar contagem por status em outro CSV
    with open(status_summary_file, 'w', newline='', encoding='utf-8') as status_file:
        fieldnames = ['Status', 'Quantidade por Status']
        writer = csv.DictWriter(status_file, fieldnames=fieldnames)

        writer.writeheader()
        for status, count in status_count.items():
            writer.writerow({'Status': status, 'Quantidade por Status': count})

    print(f"Arquivos CSV salvos na pasta '{output_dir}' com sucesso.")

# Função para criar novo CSV com status atualizados
def new_files_with_status_update():
    # Caminhos dos arquivos CSV
    input_csv = os.path.join('glpi-api', 'glpi_stats_summary.csv')
    output_csv = os.path.join('glpi-api', 'glpi_stats_summary_updated.csv')

    # Dicionário para fazer a substituição dos valores do status
    status_map = {
        '2': 'Em atendimento',
        '4': 'Pendente',
        '5': 'Solucionado',
        '6': 'Fechado'
    }

    # Atualizar tickets
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile, \
        open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Iterar sobre as linhas do CSV original
        for row in reader:
            # Se a linha tiver uma coluna Status, substituir o valor
            if row and len(row) > 1 and row[1] in status_map:
                row[1] = status_map[row[1]]
            writer.writerow(row)

    print(f'Arquivo CSV atualizado salvo como {output_csv}')

    # Atualizar também o arquivo glpi_stats_status_summary
    update_status_summary(status_map)

# Função para atualizar o arquivo de status com significados
def update_status_summary(status_map):
    # Caminhos dos arquivos CSV
    input_status_csv = os.path.join('glpi-api', 'glpi_stats_status_summary.csv')
    output_status_csv = os.path.join('glpi-api', 'glpi_stats_status_summary_updated.csv')

    # Abrir o arquivo CSV de contagem por status e o novo CSV para saída
    with open(input_status_csv, mode='r', newline='', encoding='utf-8') as infile, \
        open(output_status_csv, mode='w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Iterar sobre as linhas do CSV original
        for row in reader:
            # Se a linha tiver uma coluna Status, substituir o valor
            if row and row[0] in status_map:
                row[0] = status_map[row[0]]
            writer.writerow(row)

    print(f'Arquivo de contagem de status atualizado salvo como {output_status_csv}')

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
        tickets = get_all_recent_tickets(session_token)
        if tickets:
            save_data_to_files(tickets)
            new_files_with_status_update()
        kill_session(session_token)
    else:
        print("Não foi possível iniciar a sessão. Verifique os tokens e tente novamente.")
