import requests
import pandas as pd
from datetime import datetime

class GLPIClient:
    def __init__(self, url, user_token, app_token):
        self.url = url.rstrip('/')
        self.app_token = app_token
        self.user_token = user_token
        self.session_token = None
        self._init_session()

    def _init_session(self):
        headers = {
            'App-Token': self.app_token,
            'Authorization': f'user_token {self.user_token}'
        }
        response = requests.get(f"{self.url}/initSession", headers=headers, verify=False)
        if response.status_code == 200:
            self.session_token = response.json().get('session_token')
        else:
            raise Exception(f"Erro ao iniciar sessão no GLPI: {response.text}")

    def _get_headers(self):
        return {
            'App-Token': self.app_token,
            'Session-Token': self.session_token
        }

    def kill_session(self):
        if self.session_token:
            requests.get(f"{self.url}/killSession", headers=self._get_headers(), verify=False)

    def get_entities(self):
        """Busca a lista de entidades."""
        # limit_start=0, limit=999
        url = f"{self.url}/Entity?range=0-999"
        response = requests.get(url, headers=self._get_headers(), verify=False)
        if response.status_code == 200:
            entities = response.json()
            # Se for uma lista
            if isinstance(entities, list):
                return sorted([{"id": e["id"], "name": e["name"]} for e in entities], key=lambda x: x["name"])
        return []

    def get_tickets(self, entity_id, date_start, date_end):
        """
        Busca chamados por entidade dentro do período de datas.
        O endpoint search é mais apropriado no GLPI para filtros complexos.
        """
        # Formato de data GLPI: YYYY-MM-DD HH:MM:SS
        start_str = date_start.strftime("%Y-%m-%d 00:00:00")
        end_str = date_end.strftime("%Y-%m-%d 23:59:59")

        # Endpoint de busca (Ticket=2)
        # Criteria: Data de abertura >= start AND Data de abertura <= end AND entities_id = entity_id
        
        url = f"{self.url}/search/Ticket"
        
        # Este payload usa os parâmetros de busca do GLPI
        params = {
            'criteria[0][field]': 15, # 15 é date de abertura geralmente
            'criteria[0][searchtype]': 'morethan',
            'criteria[0][value]': start_str,
            'criteria[1][link]': 'AND',
            'criteria[1][field]': 15,
            'criteria[1][searchtype]': 'lessthan',
            'criteria[1][value]': end_str,
            'criteria[2][link]': 'AND',
            'criteria[2][field]': 80, # Entity ID
            'criteria[2][searchtype]': 'equals',
            'criteria[2][value]': entity_id,
            'forcedisplay[0]': 1, # Title
            'forcedisplay[1]': 2, # ID
            'forcedisplay[2]': 15, # Date 
            'forcedisplay[3]': 17, # Solvedate 
            'forcedisplay[4]': 24, # Solution
            'forcedisplay[5]': 5, # Technician
            'forcedisplay[6]': 61, # Satisfaction
            'range': '0-999',
            'expand_dropdowns': 'true'
        }
        
        response = requests.get(url, headers=self._get_headers(), params=params, verify=False)
        
        tickets = []
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                for item in data['data']:
                    # Format satisfaction stars
                    sat_val = str(item.get('61') or '').strip()
                    sat_stars = ""
                    if sat_val.isdigit():
                        sat_stars = "⭐" * int(sat_val)
                    else:
                        sat_stars = sat_val

                    # Remove HTML tags from solution if present (basic cleanup)
                    solution_html = str(item.get('24') or '').strip()
                    import re
                    solution_clean = re.sub('<[^<]+>', '', solution_html).replace('&nbsp;', ' ')
                    
                    tickets.append({
                        "Número": item.get('2'),
                        "Título": item.get('1'),
                        "Data de abertura": item.get('15'),
                        "Data de solução": item.get('17') or item.get('16', ''),
                        "Técnico Responsável": item.get('5', ''),
                        "Solução": solution_clean,
                        "Satisfação": sat_stars
                    })
        return tickets
