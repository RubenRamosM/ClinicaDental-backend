"""Script para verificar credenciales de usuarios"""
import requests

BASE_URL = "http://localhost:8000"

credenciales = [
    {
        "tipo": "👤 Administrador",
        "correo": "admin@clinica.com",
        "password": "admin123"
    },
    {
        "tipo": "🦷 Odontólogo (Dr. Pérez)",
        "correo": "dr.perez@clinica.com",
        "password": "odontologo123"
    },
    {
        "tipo": "🦷 Odontóloga (Dra. García)",
        "correo": "dra.garcia@clinica.com",
        "password": "odontologo123"
    },
    {
        "tipo": "🦷 Odontólogo (Dr. Martínez)",
        "correo": "dr.martinez@clinica.com",
        "password": "odontologo123"
    },
    {
        "tipo": "👨‍⚕️ Paciente (Ana López)",
        "correo": "ana.lopez@email.com",
        "password": "paciente123"
    },
    {
        "tipo": "👨‍⚕️ Paciente (Carlos Rodríguez)",
        "correo": "carlos.rodriguez@email.com",
        "password": "paciente123"
    },
    {
        "tipo": "📋 Recepcionista",
        "correo": "recepcion@clinica.com",
        "password": "recepcion123"
    }
]

print("\n" + "="*60)
print("VERIFICACION DE CREDENCIALES")
print("="*60 + "\n")

url = f"{BASE_URL}/api/v1/auth/login/"

for cred in credenciales:
    try:
        response = requests.post(url, json={
            "correo": cred["correo"],
            "password": cred["password"]
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            usuario = data.get('usuario', {})
            print(f"✓ {cred['tipo']}")
            print(f"  Email: {cred['correo']}")
            print(f"  Password: {cred['password']}")
            print(f"  Nombre: {usuario.get('nombre_completo', 'N/A')}")
            print(f"  Rol: {usuario.get('tipo_usuario_nombre', 'N/A')}")
            print()
        else:
            print(f"✗ {cred['tipo']}")
            print(f"  Email: {cred['correo']}")
            print(f"  Error: Status {response.status_code}")
            print()
    except Exception as e:
        print(f"✗ {cred['tipo']}")
        print(f"  Email: {cred['correo']}")
        print(f"  Error: {str(e)}")
        print()

print("="*60)
