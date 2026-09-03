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

    def get_users(self):
        """Busca a lista de usuários para mapear IDs para nomes."""
        url = f"{self.url}/User?range=0-999"
        response = requests.get(url, headers=self._get_headers(), verify=False)
        users = {}
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for u in data:
                    first = u.get("firstname") or ""
                    last = u.get("realname") or ""
                    name = f"{first} {last}".strip()
                    if not name:
                        name = u.get("name", "")
                    users[str(u.get("id"))] = name
        return users

    def get_tickets(self, entity_id, date_start, date_end):
        """
        Busca chamados por entidade dentro do período de datas.
        """
        start_str = date_start.strftime("%Y-%m-%d 00:00:00")
        end_str = date_end.strftime("%Y-%m-%d 23:59:59")

        url = f"{self.url}/search/Ticket"
        
        params = {
            'criteria[0][field]': 15,
            'criteria[0][searchtype]': 'morethan',
            'criteria[0][value]': start_str,
            'criteria[1][link]': 'AND',
            'criteria[1][field]': 15,
            'criteria[1][searchtype]': 'lessthan',
            'criteria[1][value]': end_str,
            'criteria[2][link]': 'AND',
            'criteria[2][field]': 80,
            'criteria[2][searchtype]': 'equals',
            'criteria[2][value]': entity_id,
            'forcedisplay[0]': 1,
            'forcedisplay[1]': 2,
            'forcedisplay[2]': 15,
            'forcedisplay[3]': 17,
            'forcedisplay[4]': 24,
            'forcedisplay[5]': 5,
            'forcedisplay[6]': 61,
            'range': '0-999',
            'expand_dropdowns': 'true'
        }
        
        # Buscar mapeamento de usuários antes
        users_map = self.get_users()
        
        response = requests.get(url, headers=self._get_headers(), params=params, verify=False)
        
        tickets = []
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                for item in data['data']:
                    sat_val = str(item.get('61') or '').strip()
                    sat_stars = ""
                    if sat_val.isdigit():
                        sat_stars = "⭐" * int(sat_val)
                    else:
                        sat_stars = sat_val

                    solution_html = str(item.get('24') or '').strip()
                    import re
                    import html
                    # Primeiro decodifica entidades HTML como &#60; para <
                    solution_clean = html.unescape(solution_html)
                    # Opcionalmente fazer duplo unescape caso esteja muito encodado
                    solution_clean = html.unescape(solution_clean)
                    # Depois aplica a remocao de tags HTML
                    solution_clean = re.sub('<[^<]+>', '', solution_clean).replace('&nbsp;', ' ').strip()
                    
                    tech_raw = str(item.get('5', ''))
                    tech_names = []
                    import ast
                    try:
                        if tech_raw.startswith('[') and tech_raw.endswith(']'):
                            tech_ids = ast.literal_eval(tech_raw)
                            for t_id in tech_ids:
                                tech_names.append(users_map.get(str(t_id), str(t_id)))
                        else:
                            tech_names.append(users_map.get(tech_raw, tech_raw))
                    except:
                        tech_names.append(tech_raw)
                        
                    tech_responsavel = ", ".join([n for n in tech_names if n and n != 'None'])

                    dt_abertura = str(item.get('15') or '')[:10]
                    dt_solucao = str(item.get('17') or item.get('16') or '')[:10]
                    
                    # Garantir a ordem das chaves conforme PDF e com datas truncadas
                    tickets.append({
                        "Número": item.get('2'),
                        "Título": item.get('1'),
                        "Data de abertura": dt_abertura,
                        "Data de solução": dt_solucao,
                        "Técnico Responsável": tech_responsavel,
                        "Solução": solution_clean,
                        "Satisfação": sat_stars
                    })
        return tickets
