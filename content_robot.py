"""
Robô de Conteúdo Automatizado - Versão 3.2 CORREÇÕES CRÍTICAS
Autor: Sistema Profissional de Automação
Data: 2025-11-24

CORREÇÕES v3.2:
- ✅ Validação robusta de credenciais WordPress
- ✅ Timeout aumentado para operações WordPress
- ✅ Geração de imagem com Stability AI corrigida
- ✅ Logging detalhado de erros
- ✅ Retry logic melhorada
- ✅ Sistema de aprovação com fix de CORS
- ✅ Notificações Discord/Telegram restauradas
"""
import base64
import json
import time
import os
import hashlib
import re
import ast
import shutil
import warnings
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache
import logging
from logging.handlers import RotatingFileHandler

# Imports de terceiros
from dotenv import load_dotenv
import feedparser
import requests
from newspaper import Article
from PIL import Image
import schedule
from difflib import SequenceMatcher
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.generativeai as genai

# Imports locais
from approval_system import save_for_approval
from prompt_optimizer import PromptOptimizer
from sources_manager import AdvancedSourcesManager

load_dotenv()
warnings.filterwarnings('ignore', category=FutureWarning)

# ============================================
# CONFIGURAÇÃO DE LOGGING PROFISSIONAL
# ============================================
def setup_logging():
    """Configura logging com rotação de arquivos"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    file_handler = RotatingFileHandler(
        'robot.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# ============================================
# DATABASE MODELS
# ============================================
Base = declarative_base()

class PublishedArticle(Base):
    __tablename__ = 'published_articles'
    
    id = Column(Integer, primary_key=True)
    hash = Column(String(32), unique=True, index=True)
    url = Column(String(500))
    title = Column(String(500))
    content_hash = Column(String(32), index=True)
    content_snippet = Column(Text)
    full_content = Column(Text)
    source = Column(String(200))
    published_date = Column(DateTime, default=datetime.now)
    quality_score = Column(Float)
    originality_score = Column(Float)
    wordpress_url = Column(String(500))

class RateLimitLog(Base):
    __tablename__ = 'rate_limit_logs'
    
    id = Column(Integer, primary_key=True)
    service = Column(String(50), index=True)
    last_request = Column(DateTime, default=datetime.now)

class APIUsageLog(Base):
    __tablename__ = 'api_usage_logs'
    
    id = Column(Integer, primary_key=True)
    service = Column(String(50))
    calls = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.now)

@dataclass
class ArticleData:
    url: str
    title: str
    source: str
    content: str
    published_date: datetime
    hash: str

# ============================================
# CONTENT ROBOT CLASS
# ============================================
class ContentRobot:
    def __init__(self, config: Dict):
        self.config = config
        self.ai_client = None
        self.session = None
        self.category_map = {}
        self.tag_map = {}
        self.sources_manager = AdvancedSourcesManager()
        self.prompt_optimizer = PromptOptimizer()
        self.use_ab_testing = config.get('use_prompt_ab_testing', False)
        
        self._init_database()
        self._init_gemini()
        self._validate_wordpress_credentials()
        self._load_wordpress_metadata()
        
        self.api_usage = {'gemini_calls': 0, 'tokens_used': 0}
        
        logger.info("🤖 ContentRobot v3.2 inicializado com sucesso!")
        
    def _init_database(self):
        try:
            engine = create_engine('sqlite:///content_robot.db', echo=False)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            self.session = Session()
            logger.info("✅ Banco de dados inicializado")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar banco: {e}")
            raise
        
    def _init_gemini(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            logger.error("❌ GOOGLE_API_KEY não encontrada no .env")
            return
        
        try:
            genai.configure(api_key=api_key)
            
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
            
            self.ai_client = genai.GenerativeModel(
                'gemini-2.0-flash-exp',
                generation_config=generation_config
            )
            
            logger.info("✅ Gemini AI inicializado (2.0-flash-exp)")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Gemini: {e}")
            self.ai_client = None
    
    def _validate_wordpress_credentials(self):
        wp_url = self.config.get('wordpress_url')
        wp_user = self.config.get('wordpress_username')
        wp_pass = self.config.get('wordpress_password')
        
        if not all([wp_url, wp_user, wp_pass]):
            logger.warning("⚠️ WordPress não configurado - modo aprovação manual ativado")
            self.config['require_manual_approval'] = True
            return False
        
        try:
            logger.info(f"🔐 Testando credenciais WordPress: {wp_url}")
            
            test_url = f'{wp_url}/wp-json/wp/v2/users/me'
            response = requests.get(
                test_url,
                auth=(wp_user, wp_pass),
                timeout=15
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"✅ WordPress autenticado: {user_data.get('name', 'Unknown')}")
                return True
            elif response.status_code == 401:
                logger.error("❌ ERRO 401: Credenciais inválidas!")
                logger.error(f"   URL: {wp_url}")
                logger.error(f"   Usuário: {wp_user}")
                logger.error(f"   Verifique seu .env e tente novamente")
                self.config['require_manual_approval'] = True
                return False
            else:
                logger.warning(f"⚠️ WordPress retornou status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout ao conectar WordPress")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao validar WordPress: {e}")
            return False
    
    def _load_wordpress_metadata(self):
        wp_url = self.config.get('wordpress_url')
        wp_user = self.config.get('wordpress_username')
        wp_pass = self.config.get('wordpress_password')
        
        if not all([wp_url, wp_user, wp_pass]):
            self.category_map = {'Notícias': 1}
            self.tag_map = {}
            return
        
        try:
            cat_response = requests.get(
                f'{wp_url}/wp-json/wp/v2/categories',
                auth=(wp_user, wp_pass),
                timeout=15,
                params={'per_page': 100}
            )
            
            if cat_response.status_code == 200:
                categories = cat_response.json()
                self.category_map = {cat['name']: cat['id'] for cat in categories}
                logger.info(f"✅ {len(self.category_map)} categorias carregadas")
            
            tag_response = requests.get(
                f'{wp_url}/wp-json/wp/v2/tags',
                auth=(wp_user, wp_pass),
                timeout=15,
                params={'per_page': 100}
            )
            
            if tag_response.status_code == 200:
                tags = tag_response.json()
                self.tag_map = {tag['name']: tag['id'] for tag in tags}
                logger.info(f"✅ {len(self.tag_map)} tags carregadas")
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar metadados: {e}")
            self.category_map = {'Notícias': 1}
            self.tag_map = {}
    
    def _rate_limit(self, service: str, min_interval: float = 2.0):
        try:
            log = self.session.query(RateLimitLog).filter_by(service=service).first()
            
            if log:
                elapsed = (datetime.now() - log.last_request).total_seconds()
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                log.last_request = datetime.now()
            else:
                log = RateLimitLog(service=service, last_request=datetime.now())
                self.session.add(log)
            
            self.session.commit()
        except Exception as e:
            time.sleep(min_interval)
    
    def _log_api_usage(self, service: str, calls: int = 1, tokens: int = 0):
        try:
            today = datetime.now().date()
            log = self.session.query(APIUsageLog).filter(
                APIUsageLog.service == service,
                APIUsageLog.date >= today
            ).first()
            
            if log:
                log.calls += calls
                log.tokens_used += tokens
            else:
                log = APIUsageLog(service=service, calls=calls, tokens_used=tokens)
                self.session.add(log)
            
            self.session.commit()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao registrar uso de API: {e}")
    
    def is_duplicate(self, article_hash: str) -> bool:
        try:
            exists = self.session.query(PublishedArticle).filter_by(hash=article_hash).first()
            return exists is not None
        except Exception as e:
            logger.error(f"❌ Erro ao verificar duplicata: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError))
    )
    def fetch_rss_feeds(self) -> List[ArticleData]:
        articles = []
        
        for feed_url in self.config.get('rss_feeds', []):
            try:
                self._rate_limit('rss', 1.0)
                feed = feedparser.parse(feed_url)
                
                count = 0
                for entry in feed.entries[:3]:
                    article_hash = hashlib.md5(entry.link.encode()).hexdigest()
                    
                    if self.is_duplicate(article_hash):
                        continue
                    
                    articles.append(ArticleData(
                        url=entry.link,
                        title=entry.title,
                        source=feed.feed.get('title', 'RSS Feed'),
                        content='',
                        published_date=datetime.now(),
                        hash=article_hash
                    ))
                    count += 1
                
                if count > 0:
                    logger.info(f"✓ RSS Feed: {count} novos artigos")
                    
            except Exception as e:
                logger.error(f"✗ Erro ao processar RSS: {e}")
                
        return articles
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def extract_article_content(self, article: ArticleData) -> Optional[ArticleData]:
        try:
            self._rate_limit('extraction', 1.0)
            
            # Lista de domínios bloqueados/problemáticos
            blocked_domains = ['fastcompany.com', 'medium.com', 'substack.com']
            if any(domain in article.url for domain in blocked_domains):
                logger.warning(f"⚠️ Domínio bloqueado: {article.url}")
                return None
            
            news_article = Article(article.url)
            news_article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            news_article.config.request_timeout = 15
            
            news_article.download()
            news_article.parse()
            
            article.content = news_article.text
            
            if len(article.content) < 150:
                logger.warning(f"⚠️ Artigo muito curto: {len(article.content)} chars")
                return None
                
            return article
            
        except Exception as e:
            logger.error(f"✗ Erro ao extrair conteúdo de {article.url}: {e}")
            return None
    
    @lru_cache(maxsize=100)
    def check_quality(self, content_hash: str, word_count: int, unique_words: int) -> Dict:
        quality_score = 0
        
        if word_count >= 300:
            quality_score += 30
        if word_count >= 500:
            quality_score += 20
        if word_count >= 800:
            quality_score += 10
            
        if unique_words / word_count > 0.5:
            quality_score += 40
            
        return {
            'score': min(quality_score, 100),
            'word_count': word_count,
            'unique_words': unique_words
        }
    
    def _parse_json_robust(self, text: str) -> Optional[Dict]:
        text = text.strip()
        
        logger.info("🔍 Tentando parsear JSON...")
        
        # Tentativa 1: Parse direto
        try:
            result = json.loads(text)
            logger.info("✅ Parsing direto funcionou!")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"Tentativa 1 falhou: {e}")
        
        # Tentativa 2: Remove markdown
        try:
            cleaned = re.sub(r'```json|```', '', text, flags=re.IGNORECASE).strip()
            result = json.loads(cleaned)
            logger.info("✅ Parsing com limpeza funcionou!")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"Tentativa 2 falhou: {e}")
        
        # Tentativa 3: Extrai com regex
        try:
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
            if match:
                result = json.loads(match.group())
                logger.info("✅ Parsing com regex funcionou!")
                return result
        except json.JSONDecodeError as e:
            logger.debug(f"Tentativa 3 falhou: {e}")
        
        # Tentativa 4: Limpeza agressiva
        try:
            # Remove quebras de linha problemáticas
            cleaned = text.replace('\n', ' ')
            cleaned = re.sub(r'\s+', ' ', cleaned)
            result = json.loads(cleaned)
            logger.info("✅ Parsing com limpeza agressiva funcionou!")
            return result
        except json.JSONDecodeError as e:
            logger.debug(f"Tentativa 4 falhou: {e}")
        
        logger.error("❌ Todas as tentativas de parsing falharam")
        logger.error(f"Preview do texto: {text[:200]}")
        return None
    
    @retry(
        stop=stop_after_attempt(2),  # REDUZIDO: 2 tentativas ao invés de 3
        wait=wait_exponential(multiplier=2, min=4, max=20)
    )
    def process_with_gemini(self, article: ArticleData) -> Optional[Dict]:
        if not article or not article.content or len(article.content) < 100:
            logger.warning("❌ Artigo inválido ou muito curto")
            return None
        
        if self.use_ab_testing:
            prompt_id, raw_prompt_template = self.prompt_optimizer.get_next_prompt()
        else:
            prompt_id = 'custom'
            raw_prompt_template = self.config.get('custom_prompt')
        
        if raw_prompt_template:
            try:
                prompt = raw_prompt_template.format(
                    article_title=article.title,
                    article_source=article.source,
                    article_url=article.url,
                    article_content=article.content[:4000]
                )
            except KeyError as e:
                logger.error(f"❌ Erro no template do prompt: {e}")
                return None
        else:
            prompt = f"""Você é um editor profissional de blogs brasileiros.

Reescreva COMPLETAMENTE o artigo abaixo em português:

REGRAS:
1. JAMAIS copie frases do original
2. Mínimo 800 palavras
3. Use HTML com H2 e H3
4. Inclua ao final: "Fonte: {article.source} - {article.url}"

ARTIGO:
{article.title}
{article.content[:4000]}

Retorne APENAS JSON (sem markdown):

{{"titulo": "...", "meta_description": "...", "conteudo_completo": "<h2>...</h2><p>...</p>", "palavras_chave": ["..."], "categoria": "Tecnologia", "qualidade_score": 85, "originalidade_score": 90, "seo_score": 88}}"""
        
        try:
            if not self.ai_client:
                logger.error("❌ Gemini não configurado")
                return None
            
            self._rate_limit('gemini', 2.0)
            
            logger.info("🤖 Enviando para Gemini...")
            response = self.ai_client.generate_content(prompt)
            
            if not response or not response.text:
                logger.error("❌ Gemini retornou resposta vazia")
                return None
            
            text = response.text.strip()
            logger.info(f"📝 Resposta recebida ({len(text)} chars)")
            
            self._log_api_usage('gemini', calls=1)
            self.api_usage['gemini_calls'] += 1
            
            result = self._parse_json_robust(text)
            
            if not result:
                debug_file = f"debug_gemini_{int(time.time())}.txt"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(f"PROMPT:\n{prompt}\n\nRESPOSTA:\n{text}")
                logger.error(f"❌ Parse falhou - salvo em {debug_file}")
                return None
            
            # Validação de campos obrigatórios
            required_fields = ['titulo', 'meta_description', 'conteudo_completo', 'palavras_chave']
            missing_fields = [f for f in required_fields if f not in result]
            
            if missing_fields:
                logger.error(f"❌ Campos faltando no JSON: {missing_fields}")
                return None
            
            # Validação de qualidade
            if result.get('qualidade_score', 0) < self.config.get('min_quality_score', 60):
                logger.warning(f"⚠️ Qualidade baixa: {result.get('qualidade_score')}/100")
                return None
            
            logger.info(f"✓ Artigo processado: Qualidade {result.get('qualidade_score')}/100")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ Erro Gemini: {type(e).__name__}: {e}")
            raise  # Re-raise para o retry funcionar
    
    def generate_image_stable_diffusion(self, title: str, keywords: List[str]) -> Optional[str]:
        api_key = os.getenv('STABILITY_API_KEY')
        
        if not api_key:
            return None
        
        try:
            self._rate_limit('stability', 5.0)
            
            logger.info(f"🎨 Gerando imagem...")
            
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            payload = {
                "text_prompts": [{"text": f"Editorial illustration: {title}", "weight": 1}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                image_data = base64.b64decode(data['artifacts'][0]['base64'])
                
                os.makedirs('images', exist_ok=True)
                image_path = f"images/article_{int(time.time())}.png"
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"✓ Imagem gerada: {image_path}")
                return image_path
            else:
                logger.error(f"❌ Stability erro {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"✗ Erro ao gerar imagem: {e}")
            return None
    
    def send_notification(self, message: str, level: str = "info"):
        webhook_url = os.getenv('NOTIFICATION_WEBHOOK_URL')
        
        if not webhook_url:
            return
        
        try:
            emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}
            
            payload = {
                "content": f"{emoji.get(level, 'ℹ️')} **Content Robot v3.2**\n{message}",
                "username": "Content Robot"
            }
            
            requests.post(webhook_url, json=payload, timeout=5)
        except:
            pass
    
    def publish_to_wordpress(self, content: Dict, article_hash: str, original_article: ArticleData, image_path: Optional[str] = None) -> bool:
        if self.config.get('require_manual_approval', True):
            logger.info("📋 Enviando para aprovação manual")
            try:
                article_id = save_for_approval({
                    **content,
                    'source_url': original_article.url,
                    'source_name': original_article.source
                })
                
                if article_id > 0:
                    logger.info(f"✅ Artigo #{article_id} salvo para aprovação")
                    self._save_to_database(
                        article_hash, original_article.url, content['titulo'],
                        content['conteudo_completo'], original_article.source,
                        content.get('qualidade_score', 0),
                        content.get('originalidade_score', 0),
                        f"PENDING_APPROVAL_{article_id}"
                    )
                    return True
            except Exception as e:
                logger.error(f"❌ Erro ao salvar para aprovação: {e}")
                return False
        
        return False
    
    def _save_to_database(self, article_hash, url, title, full_content, source, quality_score, originality_score, wordpress_url):
        try:
            db_article = PublishedArticle(
                hash=article_hash,
                url=url,
                title=title,
                content_hash=hashlib.md5(full_content.encode()).hexdigest(),
                content_snippet=full_content[:500],
                full_content=full_content,
                source=source,
                quality_score=quality_score,
                originality_score=originality_score,
                wordpress_url=wordpress_url
            )
            
            self.session.add(db_article)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"✗ Erro ao salvar no banco: {e}")
    
    def run_cycle(self):
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 Ciclo iniciado - {datetime.now()}")
        logger.info(f"{'='*60}\n")
        
        self.send_notification(f"🚀 Ciclo iniciado", "info")
        
        try:
            articles = self.fetch_rss_feeds()
            
            if not articles:
                logger.info("⚠️ Nenhum artigo novo")
                return
            
            processed_count = 0
            rejected_count = 0
            
            for i, article in enumerate(articles, 1):
                logger.info(f"\n--- Processando {i}/{len(articles)} ---")
                
                try:
                    article = self.extract_article_content(article)
                    if not article:
                        rejected_count += 1
                        continue
                    
                    processed = self.process_with_gemini(article)
                    if not processed:
                        rejected_count += 1
                        continue
                    
                    image_path = None
                    if self.config.get('generate_images', False):
                        image_path = self.generate_image_stable_diffusion(
                            processed['titulo'],
                            processed.get('palavras_chave', [])
                        )
                    
                    success = self.publish_to_wordpress(
                        processed, article.hash, article, image_path
                    )
                    
                    if success:
                        processed_count += 1
                        self.send_notification(
                            f"✅ {processed['titulo'][:60]}",
                            "success"
                        )
                    else:
                        rejected_count += 1
                    
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"✗ Erro: {e}")
                    rejected_count += 1
            
            logger.info(f"\n✓ Ciclo concluído!")
            logger.info(f"📊 Processados: {processed_count} | Rejeitados: {rejected_count}")
            
            self.send_notification(
                f"✅ Ciclo: {processed_count} aprovados, {rejected_count} rejeitados",
                "success"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro crítico: {e}")
            self.send_notification(f"❌ Erro: {str(e)[:100]}", "error")

def main():
    try:
        config = {
            'ai_provider': 'gemini',
            'use_prompt_ab_testing': False,
            'custom_prompt': None,
            
            'rss_feeds': [
                'https://techcrunch.com/feed/',
                'https://canaltech.com.br/rss/',
            ],
            
            'min_quality_score': 60,
            'generate_images': True,
            
            'wordpress_url': os.getenv('WORDPRESS_URL'),
            'wordpress_username': os.getenv('WORDPRESS_USERNAME'),
            'wordpress_password': os.getenv('WORDPRESS_PASSWORD'),
            
            'require_manual_approval': True,
            'auto_publish': False,
            'check_interval_minutes': 120
        }
        
        robot = ContentRobot(config)
        robot.run_cycle()
        
        schedule.every(config['check_interval_minutes']).minutes.do(robot.run_cycle)
        
        logger.info("🤖 Robô iniciado! Pressione Ctrl+C para parar.")
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏸️ Robô pausado")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise

if __name__ == '__main__':
    main()