"""
Script para probar subdominios y multitenancy
Ejecutar: python probar_subdominios.py
"""
import requests
import json
from colorama import init, Fore, Style

init(autoreset=True)

def probar_endpoint(url, nombre):
    """Prueba un endpoint y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"🔍 Probando: {Fore.CYAN}{nombre}")
    print(f"   URL: {Fore.YELLOW}{url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=5)
        
        print(f"✅ Status: {Fore.GREEN}{response.status_code}")
        print(f"📦 Headers:")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Server: {response.headers.get('Server', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n📄 Respuesta JSON:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except:
                print(f"\n📄 Respuesta (texto):")
                print(response.text[:500])
        elif response.status_code == 404:
            print(f"{Fore.YELLOW}⚠️  Endpoint no encontrado (normal si no hay API en /)")
        else:
            print(f"{Fore.RED}❌ Error: {response.status_code}")
            print(response.text[:500])
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}❌ Error de conexión - ¿El servidor está corriendo?")
        print(f"   Ejecuta: {Fore.CYAN}python manage.py runserver 0.0.0.0:8001 --noreload")
    except requests.exceptions.Timeout:
        print(f"{Fore.RED}❌ Timeout - El servidor tardó demasiado en responder")
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {str(e)}")

def main():
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}🧪 PRUEBA DE SUBDOMINIOS - MULTITENANCY")
    print(f"{Fore.MAGENTA}{'='*60}\n")
    
    base_port = 8001
    
    # Endpoints a probar
    tests = [
        {
            'nombre': 'Tenant Público (localhost)',
            'url': f'http://localhost:{base_port}/',
        },
        {
            'nombre': 'Tenant Público - API',
            'url': f'http://localhost:{base_port}/api/',
        },
        {
            'nombre': 'Tenant Público - Admin',
            'url': f'http://localhost:{base_port}/admin/',
        },
        {
            'nombre': 'Clínica 1 (subdominio)',
            'url': f'http://clinica1.localhost:{base_port}/',
        },
        {
            'nombre': 'Clínica 1 - API',
            'url': f'http://clinica1.localhost:{base_port}/api/',
        },
        {
            'nombre': 'Clínica 1 - Admin',
            'url': f'http://clinica1.localhost:{base_port}/admin/',
        },
    ]
    
    for test in tests:
        probar_endpoint(test['url'], test['nombre'])
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.GREEN}✅ Pruebas completadas")
    print(f"{Fore.MAGENTA}{'='*60}\n")
    
    print(f"{Fore.CYAN}💡 Notas:")
    print(f"  - Si ves 404, es normal si no hay contenido en /")
    print(f"  - Lo importante es que cada URL responda")
    print(f"  - Verifica en los logs del servidor que el schema cambie")
    print(f"  - localhost → {Fore.YELLOW}SET search_path = 'public'")
    print(f"  - clinica1.localhost → {Fore.YELLOW}SET search_path = 'clinica1'")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error fatal: {str(e)}")
