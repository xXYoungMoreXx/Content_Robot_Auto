"""
Script de Diagnóstico do Content Robot v3.2
Execute: python diagnose.py
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def test_item(name, condition, details=""):
    status = "✅" if condition else "❌"
    print(f"{status} {name}")
    if details:
        print(f"   {details}")
    return condition

def main():
    print("""
    ╔══════════════════════════════════════════╗
    ║   🔍 DIAGNÓSTICO DO CONTENT ROBOT v3.2   ║
    ║                                          ║
    ║   Testando todas as configurações...    ║
    ╚══════════════════════════════════════════╝
    """)
    
    all_ok = True
    
    # ===========================================
    # 1. VERIFICAÇÃO DE PYTHON
    # ===========================================
    print_header("1. PYTHON & DEPENDÊNCIAS")
    
    python_version = sys.version_info
    all_ok &= test_item(
        "Python 3.8+",
        python_version >= (3, 8),
        f"Versão: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )
    
    # Testa imports
    required_modules = [
        ('feedparser', 'feedparser'),
        ('newspaper', 'newspaper3k'),
        ('requests', 'requests'),
        ('PIL', 'Pillow'),
        ('schedule', 'schedule'),
        ('sqlalchemy', 'sqlalchemy'),
        ('genai', 'google-generativeai'),
        ('dotenv', 'python-dotenv'),
        ('tenacity', 'tenacity'),
        ('aiohttp', 'aiohttp'),
        ('flask', 'flask'),
        ('flask_cors', 'flask-cors')
    ]
    
    for module_name, pip_name in required_modules:
        try:
            __import__(module_name)
            test_item(f"Módulo {pip_name}", True)
        except ImportError:
            test_item(
                f"Módulo {pip_name}",
                False,
                f"Instale: pip install {pip_name}"
            )
            all_ok = False
    
    # ===========================================
    # 2. ARQUIVO .ENV
    # ===========================================
    print_header("2. ARQUIVO .ENV")
    
    env_exists = os.path.exists('.env')
    all_ok &= test_item(
        "Arquivo .env existe",
        env_exists,
        "Crie um arquivo .env na raiz do projeto" if not env_exists else ""
    )
    
    if env_exists:
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
            
        test_item(
            "GOOGLE_API_KEY",
            'GOOGLE_API_KEY' in env_content and 'sua_chave' not in env_content.lower()
        )
        
        test_item(
            "WORDPRESS_URL",
            'WORDPRESS_URL' in env_content and 'seusite' not in env_content.lower()
        )
        
        test_item(
            "WORDPRESS_USERNAME",
            'WORDPRESS_USERNAME' in env_content and 'seu_usuario' not in env_content.lower()
        )
        
        test_item(
            "WORDPRESS_PASSWORD",
            'WORDPRESS_PASSWORD' in env_content and len(os.getenv('WORDPRESS_PASSWORD', '')) > 10
        )
    
    # ===========================================
    # 3. TESTE DE GEMINI AI
    # ===========================================
    print_header("3. GEMINI AI")
    
    gemini_key = os.getenv('GOOGLE_API_KEY')
    
    if gemini_key:
        test_item("API Key encontrada", True, f"Chave: {gemini_key[:10]}...")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Teste simples
            response = model.generate_content("Responda apenas: OK")
            
            all_ok &= test_item(
                "Conexão com Gemini",
                'ok' in response.text.lower(),
                f"Resposta: {response.text[:50]}"
            )
            
        except Exception as e:
            all_ok &= test_item("Conexão com Gemini", False, str(e)[:100])
    else:
        all_ok &= test_item("API Key encontrada", False, "Configure GOOGLE_API_KEY no .env")
    
    # ===========================================
    # 4. TESTE DE WORDPRESS
    # ===========================================
    print_header("4. WORDPRESS")
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_PASSWORD')
    
    if all([wp_url, wp_user, wp_pass]):
        test_item("Credenciais encontradas", True)
        
        # Remove barra final
        wp_url = wp_url.rstrip('/')
        
        try:
            # Testa se o WordPress existe
            response = requests.get(f'{wp_url}/wp-json', timeout=10)
            
            test_item(
                "WordPress acessível",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Testa autenticação
            auth_response = requests.get(
                f'{wp_url}/wp-json/wp/v2/users/me',
                auth=(wp_user, wp_pass),
                timeout=10
            )
            
            if auth_response.status_code == 200:
                user_data = auth_response.json()
                all_ok &= test_item(
                    "Autenticação WordPress",
                    True,
                    f"Usuário: {user_data.get('name', 'Unknown')}"
                )
            elif auth_response.status_code == 401:
                all_ok &= test_item(
                    "Autenticação WordPress",
                    False,
                    "ERRO 401: Credenciais inválidas! Use Application Password"
                )
            else:
                all_ok &= test_item(
                    "Autenticação WordPress",
                    False,
                    f"Status inesperado: {auth_response.status_code}"
                )
            
            # Testa permissões de publicação
            test_post = {
                'title': 'TESTE - Content Robot - DELETE',
                'content': 'Teste de permissões',
                'status': 'draft'
            }
            
            post_response = requests.post(
                f'{wp_url}/wp-json/wp/v2/posts',
                auth=(wp_user, wp_pass),
                json=test_post,
                timeout=15
            )
            
            if post_response.status_code in [200, 201]:
                post_id = post_response.json()['id']
                test_item("Permissão de criar posts", True, f"Post teste criado (ID: {post_id})")
                
                # Deleta o post de teste
                requests.delete(
                    f'{wp_url}/wp-json/wp/v2/posts/{post_id}?force=true',
                    auth=(wp_user, wp_pass),
                    timeout=10
                )
            else:
                all_ok &= test_item(
                    "Permissão de criar posts",
                    False,
                    f"Status: {post_response.status_code}"
                )
            
        except requests.exceptions.Timeout:
            all_ok &= test_item("WordPress acessível", False, "Timeout - Site muito lento")
        except requests.exceptions.ConnectionError:
            all_ok &= test_item("WordPress acessível", False, "Erro de conexão - Verifique URL")
        except Exception as e:
            all_ok &= test_item("WordPress acessível", False, str(e)[:100])
    else:
        all_ok &= test_item(
            "Credenciais encontradas",
            False,
            "Configure WORDPRESS_URL, WORDPRESS_USERNAME e WORDPRESS_PASSWORD no .env"
        )
    
    # ===========================================
    # 5. TESTE DE STABILITY AI (OPCIONAL)
    # ===========================================
    print_header("5. STABILITY AI (Imagens)")
    
    stability_key = os.getenv('STABILITY_API_KEY')
    
    if stability_key:
        test_item("API Key encontrada", True, f"Chave: {stability_key[:10]}...")
        
        try:
            response = requests.get(
                'https://api.stability.ai/v1/user/account',
                headers={'Authorization': f'Bearer {stability_key}'},
                timeout=10
            )
            
            if response.status_code == 200:
                test_item("Conexão com Stability AI", True)
            else:
                test_item(
                    "Conexão com Stability AI",
                    False,
                    f"Status: {response.status_code}"
                )
        except Exception as e:
            test_item("Conexão com Stability AI", False, str(e)[:100])
    else:
        test_item(
            "API Key encontrada",
            False,
            "Configure STABILITY_API_KEY para gerar imagens (opcional)"
        )
    
    # ===========================================
    # 6. ARQUIVOS DO PROJETO
    # ===========================================
    print_header("6. ARQUIVOS DO PROJETO")
    
    required_files = [
        'content_robot.py',
        'approval_system.py',
        'prompt_optimizer.py',
        'sources_manager.py'
    ]
    
    for file in required_files:
        all_ok &= test_item(
            f"Arquivo {file}",
            os.path.exists(file),
            f"Baixe o arquivo do repositório" if not os.path.exists(file) else ""
        )
    
    # ===========================================
    # 7. BANCO DE DADOS
    # ===========================================
    print_header("7. BANCO DE DADOS")
    
    db_exists = os.path.exists('content_robot.db')
    
    test_item(
        "Banco de dados",
        db_exists,
        "Será criado automaticamente na primeira execução" if not db_exists else "Existente"
    )
    
    if db_exists:
        try:
            from sqlalchemy import create_engine
            engine = create_engine('sqlite:///content_robot.db')
            connection = engine.connect()
            connection.close()
            test_item("Banco acessível", True)
        except Exception as e:
            test_item("Banco acessível", False, str(e)[:100])
    
    # ===========================================
    # RESUMO FINAL
    # ===========================================
    print_header("RESUMO DO DIAGNÓSTICO")
    
    if all_ok:
        print("""
        ✅ TUDO OK! Sistema pronto para rodar.
        
        Para iniciar:
        
        Terminal 1:
        python content_robot.py
        
        Terminal 2:
        python approval_system.py
        
        Acesse: http://localhost:5001
        """)
    else:
        print("""
        ❌ PROBLEMAS DETECTADOS!
        
        Corrija os erros acima antes de executar o robô.
        
        Principais correções:
        1. Configure o arquivo .env com suas credenciais
        2. Use Application Password do WordPress (não senha normal)
        3. Instale dependências: pip install -r requirements.txt
        4. Verifique se o WordPress tem REST API ativa
        
        Leia o guia: TROUBLESHOOTING.md
        """)
    
    print(f"\n{'='*60}\n")

if __name__ == '__main__':
    main()