# 🤖 Content Robot - Automação Inteligente de Publicação de Artigos

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gemini](https://img.shields.io/badge/AI-Gemini%202.0-orange)](https://ai.google.dev/)
[![WordPress](https://img.shields.io/badge/CMS-WordPress-21759B)](https://wordpress.org/)

Sistema profissional de automação para criação e publicação de conteúdo original em WordPress usando IA generativa. Coleta notícias de fontes RSS, reescreve com IA (Gemini, Claude ou OpenAI), gera imagens e publica automaticamente ou através de sistema de aprovação manual.

---

## ✨ Principais Recursos

### 🎯 Core Features
- **Coleta Automatizada**: Busca artigos de múltiplas fontes RSS
- **Reescrita com IA**: Conteúdo 100% original usando modelos de última geração
- **Geração de Imagens**: Criação automática de imagens com Stable Diffusion
- **Sistema de Aprovação**: Interface web para revisão antes da publicação
- **Detecção de Duplicatas**: Banco de dados SQLite para evitar repetições
- **A/B Testing de Prompts**: Otimização automática dos prompts de IA
- **Dashboard Analytics**: Métricas detalhadas de performance

### 🧠 IAs Suportadas

| IA | Status | Custo | Qualidade | Recomendação |
|---|---|---|---|---|
| **Google Gemini 2.0** | ✅ Padrão | Gratuito (60 req/min) | ⭐⭐⭐⭐⭐ | **Recomendado** |
| **Anthropic Claude 3.5** | 🔧 Configurável | Pago ($3/1M tokens) | ⭐⭐⭐⭐⭐ | Qualidade Premium |
| **OpenAI GPT-4** | 🔧 Configurável | Pago ($30/1M tokens) | ⭐⭐⭐⭐⭐ | Versátil |
| **OpenAI GPT-4o-mini** | 🔧 Configurável | Econômico ($0.15/1M tokens) | ⭐⭐⭐⭐ | Custo-benefício |
| **Stability AI** | 🎨 Imagens | ~$0.02/imagem | ⭐⭐⭐⭐ | Geração de capas |

> **💡 Dica**: O Gemini 2.0 é **gratuito** e oferece excelente qualidade. Ideal para começar!

---

## 🚀 Instalação Rápida

### Pré-requisitos
- Python 3.8 ou superior
- Site WordPress com REST API ativa
- Chaves de API (ver seção abaixo)

### Passo 1: Clone o Repositório
```bash
git clone https://github.com/seu-usuario/content-robot.git
cd content-robot
```

### Passo 2: Instale as Dependências
```bash
pip install -r requirements.txt
```

### Passo 3: Configure o `.env`
```bash
cp .env.example .env
# Edite o .env com suas credenciais
```

**Configuração Mínima (.env)**:
```env
# IA - Escolha UMA das opções:
GOOGLE_API_KEY=sua_chave_gemini  # GRATUITO - Recomendado
# ANTHROPIC_API_KEY=sk-ant-xxx  # OU Claude (pago)
# OPENAI_API_KEY=sk-xxx          # OU OpenAI (pago)

# WordPress (obrigatório)
WORDPRESS_URL=https://seusite.com
WORDPRESS_USERNAME=seu_usuario
WORDPRESS_PASSWORD=xxxx xxxx xxxx xxxx  # Application Password

# Imagens (opcional)
STABILITY_API_KEY=sk-xxx  # Deixe vazio se não quiser gerar imagens
```

### Passo 4: Execute o Diagnóstico
```bash
python diagnose.py
```

### Passo 5: Inicie o Sistema
```bash
# Terminal 1: Robô de Conteúdo
python content_robot.py

# Terminal 2: Sistema de Aprovação
python approval_system.py

# Terminal 3: Dashboard (opcional)
python dashboard.py
```

**Ou use o script único**:
```bash
# Windows
start_all.bat

# Linux/Mac
./start_all.sh
```

---

## 🔑 Obtendo Chaves de API

### 1. Google Gemini (Gratuito - Recomendado)
1. Acesse: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Clique em "Get API Key"
3. Copie a chave e adicione no `.env`

**Limites**: 60 requisições/minuto (gratuito)

### 2. Anthropic Claude (Pago)
1. Acesse: [Anthropic Console](https://console.anthropic.com/)
2. Crie uma conta e adicione créditos
3. Gere uma API key em "API Keys"

**Custo**: ~$3 por 1 milhão de tokens

### 3. OpenAI GPT (Pago)
1. Acesse: [OpenAI Platform](https://platform.openai.com/)
2. Adicione créditos de pagamento
3. Crie uma API key

**Custo**: 
- GPT-4: $30/1M tokens
- GPT-4o-mini: $0.15/1M tokens (econômico)

### 4. Stability AI (Imagens - Opcional)
1. Acesse: [Stability AI](https://platform.stability.ai/)
2. Cadastre-se e adicione créditos
3. Gere uma API key

**Custo**: ~$0.02 por imagem

### 5. WordPress Application Password
1. Acesse: **WP Admin → Usuários → Seu Perfil**
2. Role até "Application Passwords"
3. Digite um nome (ex: "Content Robot") e clique "Add New"
4. **Copie a senha gerada** (formato: `xxxx xxxx xxxx xxxx`)
5. Use essa senha no `.env` (não a senha normal!)

---

## ⚙️ Configuração Avançada

### Selecionando a IA no `content_robot.py`

Edite a função `_init_ai()` no arquivo `content_robot.py`:

```python
def _init_ai(self):
    """Inicializa o cliente de IA"""
    
    # OPÇÃO 1: Gemini (GRATUITO - Padrão)
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.ai_client = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini 2.0 inicializado (GRATUITO)")
        return
    
    # OPÇÃO 2: Claude (PAGO - Alta Qualidade)
    # api_key = os.getenv('ANTHROPIC_API_KEY')
    # if api_key:
    #     from anthropic import Anthropic
    #     self.ai_client = Anthropic(api_key=api_key)
    #     self.ai_model = 'claude-3-5-sonnet-20241022'
    #     logger.info("✅ Claude 3.5 Sonnet inicializado")
    #     return
    
    # OPÇÃO 3: OpenAI (PAGO - Versátil)
    # api_key = os.getenv('OPENAI_API_KEY')
    # if api_key:
    #     from openai import OpenAI
    #     self.ai_client = OpenAI(api_key=api_key)
    #     self.ai_model = 'gpt-4o-mini'  # ou 'gpt-4' para máxima qualidade
    #     logger.info("✅ OpenAI GPT inicializado")
    #     return
```

### A/B Testing de Prompts

Ative no `main()`:
```python
config = {
    'use_prompt_ab_testing': True,  # Testa 5 estilos diferentes
    # ...
}
```

Veja estatísticas:
```bash
python prompt_optimizer.py
```

### Fontes de Notícias Adicionais

Adicione mais fontes no `sources_manager.py`:
```python
manager = AdvancedSourcesManager()

# RSS Feeds especializados
feeds = manager.get_specialized_feeds(niche='finance')

# APIs de notícias
articles = manager.fetch_currents_api()
articles = manager.fetch_gnews()
articles = manager.fetch_medium_topic('technology')
```

---

## 📊 Dashboard e Monitoramento

### Interfaces Web

| Interface | URL | Função |
|---|---|---|
| **Sistema de Aprovação** | `http://localhost:5001` | Revisar e aprovar artigos |
| **Dashboard Analytics** | `http://localhost:5000` | Métricas e estatísticas |

### Logs

Todos os eventos são registrados em `robot.log`:
```bash
tail -f robot.log  # Linux/Mac
Get-Content robot.log -Wait  # Windows PowerShell
```

---

## 🎨 Exemplos de Prompts

O sistema inclui 5 estilos pré-configurados de prompts:

1. **Jornalístico Formal**: Investigativo, baseado em dados
2. **Casual e Acessível**: Storytelling, didático
3. **Clickbait Educativo**: Viral mas informativo
4. **SEO Máximo**: Otimizado para ranqueamento
5. **Análise Profunda**: Técnico, relatórios detalhados

Edite em `prompt_optimizer.py` ou crie seu próprio prompt customizado.

---

## 🔧 Troubleshooting

### Erro 401 no WordPress
**Problema**: Credenciais inválidas
**Solução**: Use **Application Password**, não a senha normal!

```bash
python diagnose.py  # Testa autenticação
```

### Gemini não responde
**Problema**: API key inválida ou limite excedido
**Solução**: 
1. Verifique a chave em [Google AI Studio](https://makersuite.google.com/)
2. Aguarde se excedeu 60 req/min

### Erro de parsing JSON
**Problema**: IA retornou formato inválido
**Solução**: O sistema já possui 6 estratégias de fallback. Verifique `debug_gemini_*.txt` para análise.

### Imagens não são geradas
**Problema**: `STABILITY_API_KEY` não configurada
**Solução**: 
1. Configure a chave OU
2. Desative geração: `'generate_images': False` no config

---

## 📁 Estrutura do Projeto

```
content-robot/
├── content_robot.py          # Core: lógica principal
├── approval_system.py        # Interface de aprovação
├── dashboard.py              # Dashboard analytics
├── prompt_optimizer.py       # A/B testing de prompts
├── sources_manager.py        # Fontes adicionais de notícias
├── diagnose.py               # Script de diagnóstico
├── requirements.txt          # Dependências Python
├── .env                      # Credenciais (não commitar!)
├── .gitignore               # Arquivos ignorados
└── README.md                 # Este arquivo
```

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🌟 Features Planejadas

- [ ] Suporte a mais IAs (Mistral, Llama, etc.)
- [ ] Publicação em múltiplas plataformas (Medium, Ghost)
- [ ] Análise de sentimento de comentários
- [ ] Sugestão automática de tópicos trending
- [ ] Tradução automática multilíngue
- [ ] Integração com redes sociais

---

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/content-robot/issues)
- **Documentação**: [Wiki do Projeto](https://github.com/seu-usuario/content-robot/wiki)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/content-robot/discussions)

---

## 🙏 Agradecimentos

- [Google Gemini](https://ai.google.dev/) - IA generativa gratuita
- [Anthropic Claude](https://www.anthropic.com/) - IA de alta qualidade
- [OpenAI](https://openai.com/) - Pioneiros em IA generativa
- [Stability AI](https://stability.ai/) - Geração de imagens
- [WordPress](https://wordpress.org/) - CMS de código aberto

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela! ⭐**

Feito com ❤️ e muito ☕

</div>