"""
Script de Teste Individual de Componentes
Execute: python test_components.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_stability():
    """Testa Stability AI"""
    print("\n" + "="*60)
    print("  🎨 TESTE: STABILITY AI")
    print("="*60)
    
    api_key = os.getenv('STABILITY_API_KEY')
    
    if not api_key:
        print("❌ STABILITY_API_KEY não encontrada no .env")
        return False
    
    print(f"✅ API Key: {api_key[:15]}...")
    
    try:
        # Testa conta
        response = requests.get(
            'https://api.stability.ai/v1/user/account',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conta ativa: {data.get('email')}")
            print(f"💰 Créditos: {data.get('credits')}")
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def test_discord():
    """Testa Discord Webhook"""
    print("\n" + "="*60)
    print("  📱 TESTE: DISCORD WEBHOOK")
    print("="*60)
    
    webhook = os.getenv('NOTIFICATION_WEBHOOK_URL')
    
    if not webhook:
        print("❌ NOTIFICATION_WEBHOOK_URL não encontrada")
        return False
    
    try:
        payload = {
            "content": "🧪 **TESTE** - Content Robot\n\nSe você recebeu esta mensagem, as notificações funcionam!",
            "username": "Content Robot - TESTE"
        }
        
        response = requests.post(webhook, json=payload, timeout=5)
        
        if response.status_code in [200, 204]:
            print("✅ Mensagem enviada! Verifique seu Discord")
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def test_gemini():
    """Testa Gemini AI"""
    print("\n" + "="*60)
    print("  🤖 TESTE: GEMINI AI")
    print("="*60)
    
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ GOOGLE_API_KEY não encontrada")
        return False
    
    print(f"✅ API Key: {api_key[:15]}...")
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content("Responda apenas: OK")
        
        if 'ok' in response.text.lower():
            print(f"✅ Resposta: {response.text}")
            return True
        else:
            print(f"❌ Resposta inesperada: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def test_wordpress():
    """Testa WordPress"""
    print("\n" + "="*60)
    print("  📝 TESTE: WORDPRESS")
    print("="*60)
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        print("❌ Credenciais WordPress não configuradas")
        return False
    
    try:
        response = requests.get(
            f'{wp_url}/wp-json/wp/v2/users/me',
            auth=(wp_user, wp_pass),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Autenticado: {data.get('name')}")
            return True
        elif response.status_code == 401:
            print("❌ ERRO 401: Credenciais inválidas!")
            print("   Use Application Password, não senha normal")
            return False
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def main():
    print("""
    ╔══════════════════════════════════════════╗
    ║   🧪 TESTE DE COMPONENTES v3.2          ║
    ║                                          ║
    ║   Testando cada funcionalidade...       ║
    ╚══════════════════════════════════════════╝
    """)
    
    results = {
        'Stability AI': test_stability(),
        'Discord': test_discord(),
        'Gemini AI': test_gemini(),
        'WordPress': test_wordpress()
    }
    
    print("\n" + "="*60)
    print("📊 RESULTADO DOS TESTES")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{status} - {name}")
    
    total = len(results)
    passed_count = sum(results.values())
    
    print(f"\n📈 Total: {passed_count}/{total} testes passaram")
    
    if passed_count == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("   Seu sistema está 100% operacional!")
    else:
        print("\n⚠️ Alguns testes falharam")
        print("   Veja os erros acima e corrija")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    main()