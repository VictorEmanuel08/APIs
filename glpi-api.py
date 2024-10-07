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
        'criteria[0][field]': '15',  
        'criteria[0][searchtype]': 'morethan',
        'criteria[0][value]': seven_days_ago,
        'sort': '15',
        'order': 'DESC',
        'forcedisplay[0]': '2',
        'forcedisplay[1]': '1',
        'forcedisplay[2]': '12',
        'forcedisplay[3]': '15',
        'forcedisplay[4]': '7',
        'forcedisplay[5]': '18',  # Campo de Close Date
        'range': '0-999999'
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code in [200, 206]:
        tickets = response.json().get('data', [])
        return tickets
    else:
        print(f"Erro ao buscar chamados: {response.status_code} - {response.text}")
        return []

# Função para buscar todos os chamados de um mês específico
def get_tickets_by_month(session_token, year, month):
    start_date = datetime(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1)  

    url = f"{base_url}/search/Ticket"
    headers = {
        'App-Token': app_token,
        'Session-Token': session_token,
        'Content-Type': 'application/json'
    }

    params = {
        'criteria[0][field]': '15',
        'criteria[0][searchtype]': 'morethan',
        'criteria[0][value]': start_date.strftime('%Y-%m-%d %H:%M:%S'),
        'criteria[1][field]': '15',
        'criteria[1][searchtype]': 'lessthan',
        'criteria[1][value]': end_date.strftime('%Y-%m-%d %H:%M:%S'),
        'sort': '15',
        'order': 'DESC',
        'forcedisplay[0]': '2',
        'forcedisplay[1]': '1',
        'forcedisplay[2]': '12',
        'forcedisplay[3]': '15',
        'forcedisplay[4]': '7',
        'forcedisplay[5]': '18',  # Campo de Close Date
        'range': '0-999999'
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code in [200, 206]:
        tickets = response.json().get('data', [])
        return tickets
    else:
        print(f"Erro ao buscar chamados: {response.status_code} - {response.text}")
        return []

# Função para buscar todos os chamados do ano
def get_all_tickets_year(session_token, year):
    all_tickets = []
    for month in range(1, 13):
        monthly_tickets = get_tickets_by_month(session_token, year, month)
        all_tickets.extend(monthly_tickets)
        save_monthly_csv(monthly_tickets, year, month)
    return all_tickets

# Função para salvar tickets mensais em CSV e atualizar os status
def save_monthly_csv(tickets, year, month):
    if not tickets:
        return

    # Diretórios para salvar os arquivos
    network_dir = os.path.join(r'\\munique\Bonn\Fontes de Dados\APIs\glpi-api', f'{month:02d}-{year}')
    local_dir = os.path.join('glpi-api', f'{month:02d}-{year}')

    # Criação dos diretórios caso não existam
    if not os.path.exists(network_dir):
        os.makedirs(network_dir)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # Caminhos completos dos arquivos
    network_file = os.path.join(network_dir, f'glpi_stats_summary_{month:02d}-{year}.csv')
    local_file = os.path.join(local_dir, f'glpi_stats_summary_{month:02d}-{year}.csv')

    # Salvando o arquivo CSV em dois locais
    for file_path in [network_file, local_file]:
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Title', 'Status', 'Category', 'Open Date', 'Close Date']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for ticket in tickets:
                title = ticket.get('1', 'Nome não encontrado').replace("\n", " ").replace("\r", " ")

                ticket_info = {
                    'Title': title,
                    'Status': ticket.get('12', 'Status não encontrado'),
                    'Category': ticket.get('7', 'Categoria não encontrada'),
                    'Open Date': ticket.get('15', 'Data de abertura não encontrada'),
                    'Close Date': ticket.get('18', 'Data de fechamento não encontrada')  # Nova coluna para a Close Date
                }
                writer.writerow(ticket_info)

    print(f"Arquivo CSV mensal salvo em '{network_file}' e '{local_file}'.")

    # Salvar também o status e categorias para este mês
    save_status_csv(tickets, network_dir, local_dir)
    generate_categories_csv(tickets, network_dir, local_dir)

    # Atualizar o CSV mensal com status
    update_monthly_status_csv(network_file)
    update_monthly_status_csv(local_file)

# Função para atualizar o arquivo CSV mensal com status significativos
def update_monthly_status_csv(csv_file):
    # Dicionário para fazer a substituição dos valores do status
    status_map = {
        '2': 'Em atendimento',
        '4': 'Pendente',
        '5': 'Solucionado',
        '6': 'Fechado'
    }

    updated_file = csv_file.replace('.csv', '_updated.csv')

    with open(csv_file, mode='r', newline='', encoding='utf-8') as infile, \
         open(updated_file, mode='w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        # Iterar sobre as linhas do CSV original
        for row in reader:
            # Se a linha tiver uma coluna Status, substituir o valor
            if row and len(row) > 1 and row[1] in status_map:
                row[1] = status_map[row[1]]
            writer.writerow(row)

    print(f'Arquivo CSV atualizado salvo como {updated_file}')

def save_csv_file(filepath, fieldnames, data):
    """
    Função auxiliar para salvar dados em um arquivo CSV.
    :param filepath: Caminho do arquivo a ser salvo.
    :param fieldnames: Nomes das colunas do CSV.
    :param data: Dados a serem escritos no CSV.
    """
    with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Função para salvar dados em CSV
def save_data_to_files(tickets):
    local_dir = 'glpi-api'
    network_dir = r'\\munique\Bonn\Fontes de Dados\APIs\glpi-api'
    
    # Garantir que os diretórios existem
    for directory in [local_dir, network_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)

    filtered_tickets = []
    status_count = {}

    for ticket in tickets:
        title = ticket.get('1', 'Nome não encontrado').replace("\n", " ").replace("\r", " ")
        ticket_info = {
            'Title': title,
            'Status': ticket.get('12', 'Status não encontrado'),
            'Category': ticket.get('7', 'Categoria não encontrada'),
            'Open Date': ticket.get('15', 'Data de abertura não encontrada'),
            'Close Date': ticket.get('18', 'Data de fechamento não encontrada')
        }
        filtered_tickets.append(ticket_info)

        # Contabilizar status
        status = ticket_info['Status']
        status_count[status] = status_count.get(status, 0) + 1

    # Definir os arquivos e colunas
    summary_file = 'glpi_stats_summary.csv'
    status_summary_file = 'glpi_stats_status_summary.csv'
    summary_fieldnames = ['Title', 'Status', 'Category', 'Open Date', 'Close Date']
    status_fieldnames = ['Status', 'Quantidade por Status']

    # Dados de status no formato correto para CSV
    status_data = [{'Status': status, 'Quantidade por Status': count} for status, count in status_count.items()]

    # Salvar arquivos CSV em ambos os diretórios
    for directory in [local_dir, network_dir]:
        save_csv_file(os.path.join(directory, summary_file), summary_fieldnames, filtered_tickets)
        save_csv_file(os.path.join(directory, status_summary_file), status_fieldnames, status_data)

    print(f"Arquivos CSV salvos nas pastas '{local_dir}' e '{network_dir}' com sucesso.")

# Função para salvar status em CSV
def save_status_csv(tickets, network_dir, local_dir):
    status_count = {}
    for ticket in tickets:
        status = ticket.get('12', 'Status não encontrado')
        if status in status_count:
            status_count[status] += 1
        else:
            status_count[status] = 1

    for dir_path in [network_dir, local_dir]:
        status_file = os.path.join(dir_path, 'glpi_status_summary.csv')

        with open(status_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Status', 'Quantidade'])

            for status, count in status_count.items():
                writer.writerow([status, count])

        print(f"Arquivo de status salvo em '{status_file}'.")

# Função para gerar CSV de categorias
def generate_categories_csv(tickets, network_dir, local_dir):
    category_count = {}
    for ticket in tickets:
        category = ticket.get('7', 'Categoria não encontrada')
        if category in category_count:
            category_count[category] += 1
        else:
            category_count[category] = 1

    for dir_path in [network_dir, local_dir]:
        categories_file = os.path.join(dir_path, 'glpi_categories_summary.csv')

        with open(categories_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Categoria', 'Quantidade'])
            for category, count in category_count.items():
                writer.writerow([category, count])

        print(f"Arquivo de categorias salvo em '{categories_file}'.")

# Função para salvar dados dos últimos 7 dias em CSV
def save_last_7_days_data(tickets):
    # Diretórios para salvar os arquivos
    network_dir = r'\\munique\Bonn\Fontes de Dados\APIs\glpi-api\last_7_days'
    local_dir = 'glpi-api/last_7_days'

    if not os.path.exists(network_dir):
        os.makedirs(network_dir)
        
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # Caminhos completos dos arquivos
    network_file = os.path.join(network_dir, 'glpi_stats_summary_last_7_days.csv')
    local_file = os.path.join(local_dir, 'glpi_stats_summary_last_7_days.csv')

    # Salvando o arquivo CSV em dois locais
    for file_path in [network_file, local_file]:
        with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['Title', 'Status', 'Category', 'Open Date', 'Close Date']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()
            for ticket in tickets:
                title = ticket.get('1', 'Nome não encontrado').replace("\n", " ").replace("\r", " ")

                ticket_info = {
                    'Title': title,
                    'Status': ticket.get('12', 'Status não encontrado'),
                    'Category': ticket.get('7', 'Categoria não encontrada'),
                    'Open Date': ticket.get('15', 'Data de abertura não encontrada'),
                    'Close Date': ticket.get('18', 'Data de fechamento não encontrada')
                }
                writer.writerow(ticket_info)

    print(f"Arquivos CSV de últimos 7 dias salvos em '{network_file}' e '{local_file}'.")

    # Salvar também o status e categorias para os últimos 7 dias
    save_status_csv(tickets, network_dir, local_dir)
    generate_categories_csv(tickets, network_dir, local_dir)

def main():
    session_token = init_session()
    if session_token:
        recent_tickets = get_all_recent_tickets(session_token)
        save_last_7_days_data(recent_tickets)
        all_tickets = get_all_tickets_year(session_token, 2024)
        save_data_to_files(all_tickets)
        print("Processo concluído.")

if __name__ == "__main__":
    main()
