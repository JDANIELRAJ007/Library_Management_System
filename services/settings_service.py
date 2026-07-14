import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

def get_setting(key, default=None):
    if not os.path.exists(SETTINGS_FILE):
        return default
    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            return data.get(key, default)
    except Exception:
        return default

def set_setting(key, value):
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
        except Exception:
            pass
    data[key] = value
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
