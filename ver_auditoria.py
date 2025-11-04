import requests

# Login
login = requests.post('http://localhost:8001/api/v1/auth/login/', 
                      json={'correo': 'admin@clinica.com', 'password': 'admin123'})
token = login.json()['token']

# Consultar auditoría
audit = requests.get('http://localhost:8001/api/v1/auditoria/?limit=20', 
                     headers={'Authorization': f'Token {token}'})

data = audit.json()
print(f'\n✅ TOTAL REGISTROS EN AUDITORÍA: {data.get("count", 0)}\n')
print('📋 Últimas 20 acciones registradas:\n')

for i, x in enumerate(data.get('results', []), 1):
    print(f'{i:2}. {x.get("accion", "N/A"):50} | {x.get("tabla_afectada", "N/A"):20} | {x.get("fecha", "N/A")[:19]}')
