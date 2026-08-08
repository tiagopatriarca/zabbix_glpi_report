import streamlit as st
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config_data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

def get_zabbix_config():
    config = load_config()
    return config.get("zabbix", {})

def get_glpi_config():
    config = load_config()
    return config.get("glpi", {})
