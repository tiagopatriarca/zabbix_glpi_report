from pyzabbix import ZabbixAPI
import pandas as pd
from datetime import datetime
import streamlit as st

class ZabbixClient:
    def __init__(self, url, user, password):
        # Allow connecting even without valid SSL certs for internal networks if needed, but standard is better
        self.url = url
        self.zapi = ZabbixAPI(url)
        self.zapi.session.verify = False # Often needed for internal Zabbix servers with self-signed certs
        self.zapi.login(user, password)

    def get_hostgroups(self):
        """Busca todos os grupos de hosts."""
        groups = self.zapi.hostgroup.get(output=["groupid", "name"])
        return sorted(groups, key=lambda x: x["name"])

    def get_hosts_by_group(self, groupid):
        """Busca os hosts que pertencem a um grupo específico."""
        hosts = self.zapi.host.get(
            groupids=groupid,
            output=["hostid", "name", "status"]
        )
        return sorted(hosts, key=lambda x: x["name"])

    def get_active_alerts(self, hostid):
        """Busca alertas (triggers) ativos de um host."""
        triggers = self.zapi.trigger.get(
            hostids=hostid,
            output=["triggerid", "description", "priority", "lastchange", "value"],
            filter={"value": 1}, # Apenas problemas (value=1)
            expandDescription=True
        )
        
        alerts = []
        for t in triggers:
            alerts.append({
                "Descrição": t["description"],
                "Prioridade": self._map_priority(t["priority"]),
                "Início": datetime.fromtimestamp(int(t["lastchange"])).strftime('%d/%m/%Y %H:%M:%S')
            })
        return alerts
    
    def get_alerts_history(self, hostid, time_from, time_till):
        """Busca histórico de eventos de problemas para o host no período."""
        # This requires querying events
        events = self.zapi.event.get(
            hostids=hostid,
            time_from=int(time_from.timestamp()),
            time_till=int(time_till.timestamp()),
            output=["eventid", "name", "clock", "severity"],
            source=0, # events created by a trigger
            object=0  # trigger
        )
        
        history = []
        for e in events:
            history.append({
                "Alerta": e["name"],
                "Severidade": self._map_priority(e["severity"]),
                "Data/Hora": datetime.fromtimestamp(int(e["clock"])).strftime('%d/%m/%Y %H:%M:%S')
            })
        return history

    def get_items_by_key(self, hostid, search_key):
        """Busca items do host por chave."""
        return self.zapi.item.get(
            hostids=hostid,
            search={"key_": search_key},
            output=["itemid", "name", "key_", "value_type", "units"]
        )

    def search_items_by_name(self, hostid, search_string):
        """Busca items do host por parte do nome (case-insensitive)."""
        return self.zapi.item.get(
            hostids=hostid,
            search={"name": search_string},
            output=["itemid", "name", "key_", "value_type", "units"],
            sortfield="name"
        )

    def get_history_data(self, itemid, value_type, time_from, time_till):
        """Busca os dados históricos (gráficos) de um item."""
        history = self.zapi.history.get(
            itemids=[itemid],
            history=value_type,
            time_from=int(time_from.timestamp()),
            time_till=int(time_till.timestamp()),
            output="extend"
        )
        
        data = []
        for h in history:
            data.append({
                "time": datetime.fromtimestamp(int(h["clock"])),
                "value": float(h["value"])
            })
        return pd.DataFrame(data)

    def _map_priority(self, priority_id):
        mapping = {
            "0": "Não Classificado",
            "1": "Informação",
            "2": "Aviso",
            "3": "Média",
            "4": "Alta",
            "5": "Desastre"
        }
        return mapping.get(str(priority_id), "Desconhecido")
