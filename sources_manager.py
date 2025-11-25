"""
Gerenciador Avançado de Fontes de Notícias
Adicione APIs especializadas para seu nicho
"""
import requests
from typing import List, Dict
from datetime import datetime
import os
from dotenv import load_dotenv
import feedparser

load_dotenv()

class AdvancedSourcesManager:
    """Gerencia fontes adicionais de conteúdo"""
    
    def __init__(self):
        self.apis = {
            'newsapi': os.getenv('NEWS_API_KEY'),
            'currents': os.getenv('CURRENTS_API_KEY'),
            'gnews': os.getenv('GNEWS_API_KEY'),
        }
    
    # ==========================================
    # 1. CURRENTS API (Alternativa ao NewsAPI)
    # ==========================================
    def fetch_currents_api(self, category='business', language='pt') -> List[Dict]:
        """
        Currents API - Gratuito até 600 req/dia
        Cadastro: https://currentsapi.services/en
        """
        api_key = self.apis.get('currents')
        if not api_key:
            return []
        
        try:
            url = 'https://api.currentsapi.services/v1/latest-news'
            params = {
                'apiKey': api_key,
                'language': language,
                'category': category
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for item in data.get('news', [])[:5]:
                    articles.append({
                        'url': item['url'],
                        'title': item['title'],
                        'source': f"Currents - {item.get('author', 'Unknown')}",
                        'content': item.get('description', ''),
                        'published_date': datetime.now()
                    })
                
                return articles
        except Exception as e:
            print(f"Erro ao buscar Currents API: {e}")
            return []
    
    # ==========================================
    # 2. GNEWS API (Notícias Internacionais)
    # ==========================================
    def fetch_gnews(self, topic='business', lang='pt') -> List[Dict]:
        """
        GNews API - Gratuito até 100 req/dia
        Cadastro: https://gnews.io/
        """
        api_key = self.apis.get('gnews')
        if not api_key:
            return []
        
        try:
            url = 'https://gnews.io/api/v4/top-headlines'
            params = {
                'token': api_key,
                'lang': lang,
                'topic': topic,
                'max': 5
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for item in data.get('articles', []):
                    articles.append({
                        'url': item['url'],
                        'title': item['title'],
                        'source': f"GNews - {item['source']['name']}",
                        'content': item.get('description', ''),
                        'published_date': datetime.now()
                    })
                
                return articles
        except Exception as e:
            print(f"Erro ao buscar GNews: {e}")
            return []
    
    # ==========================================
    # 3. FEEDS RSS ESPECIALIZADOS (Gratuito)
    # ==========================================
    def get_specialized_feeds(self, niche='finance') -> List[str]:
        """
        Retorna feeds RSS especializados por nicho
        """
        feeds = {
            'finance': [
                'https://www.investing.com/rss/news.rss',
                'https://www.bloomberg.com/feed/podcast/etf-report.xml',
                'https://www.cnbc.com/id/10000664/device/rss/rss.html',
                'https://seekingalpha.com/feed.xml',
                'https://www.marketwatch.com/rss/topstories',
            ],
            'crypto': [
                'https://cointelegraph.com/rss',
                'https://www.coindesk.com/arc/outboundfeeds/rss/',
                'https://cryptopotato.com/feed/',
                'https://bitcoinmagazine.com/.rss/full/',
                'https://decrypt.co/feed',
            ],
            'tech': [
                'https://techcrunch.com/feed/',
                'https://www.theverge.com/rss/index.xml',
                'https://arstechnica.com/feed/',
                'https://www.wired.com/feed/rss',
                'https://www.engadget.com/rss.xml',
            ],
            'business': [
                'https://feeds.fortune.com/fortune/headlines',
                'https://www.entrepreneur.com/latest.rss',
                'https://www.inc.com/rss/',
                'https://hbr.org/feeds/most-popular',
                'https://www.fastcompany.com/latest/rss',
            ],
            'brazil_finance': [
                'https://www.infomoney.com.br/feed/',
                'https://www.valor.com.br/rss',
                'https://economia.uol.com.br/ultimas/index.rss',
                'https://www.seudinheiro.com/feed/',
                'https://investnews.com.br/feed/',
            ],
            'brazil_tech': [
                'https://canaltech.com.br/rss/',
                'https://www.tecmundo.com.br/rss',
                'https://olhardigital.com.br/feed/',
                'https://www.b9.com.br/feed/',
                'https://braziljournal.com/feed/',
            ]
        }
        
        return feeds.get(niche, [])
    
    # ==========================================
    # 4. MEDIUM.COM (Artigos de Qualidade)
    # ==========================================
    def fetch_medium_topic(self, topic='finance') -> List[Dict]:
        """
        Busca artigos do Medium por tópico via RSS
        """
        try:
            url = f'https://medium.com/feed/tag/{topic}'
            feed = feedparser.parse(url)
            
            articles = []
            for entry in feed.entries[:5]:
                articles.append({
                    'url': entry.link,
                    'title': entry.title,
                    'source': f'Medium - {topic}',
                    'content': entry.get('summary', ''),
                    'published_date': datetime.now()
                })
            
            return articles
        except Exception as e:
            print(f"Erro ao buscar Medium: {e}")
            return []
    
    # ==========================================
    # 5. DEV.TO (Artigos de Tecnologia)
    # ==========================================
    def fetch_devto_articles(self, tag='python', per_page=5) -> List[Dict]:
        """
        Dev.to - Artigos de programação (API gratuita)
        Documentação: https://developers.forem.com/api/
        """
        try:
            url = f'https://dev.to/api/articles?tag={tag}&per_page={per_page}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for item in data:
                    articles.append({
                        'url': item['url'],
                        'title': item['title'],
                        'source': f"Dev.to - {item['user']['name']}",
                        'content': item.get('description', ''),
                        'published_date': datetime.now()
                    })
                
                return articles
        except Exception as e:
            print(f"Erro ao buscar Dev.to: {e}")
            return []
    
    # ==========================================
    # 6. HACKER NEWS (Top Stories)
    # ==========================================
    def fetch_hackernews_top(self, limit=10) -> List[Dict]:
        """
        Hacker News - Top stories (API gratuita)
        """
        try:
            # Busca IDs das top stories
            url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                story_ids = response.json()[:limit]
                articles = []
                
                for story_id in story_ids:
                    story_url = f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json'
                    story_response = requests.get(story_url, timeout=5)
                    
                    if story_response.status_code == 200:
                        story = story_response.json()
                        
                        if story.get('url'):
                            articles.append({
                                'url': story['url'],
                                'title': story['title'],
                                'source': 'Hacker News',
                                'content': story.get('text', ''),
                                'published_date': datetime.now()
                            })
                
                return articles
        except Exception as e:
            print(f"Erro ao buscar Hacker News: {e}")
            return []
    
    # ==========================================
    # 7. WIKIPEDIA TRENDING (Tópicos em Alta)
    # ==========================================
    def fetch_wikipedia_trending(self) -> List[Dict]:
        """
        Wikipedia - Artigos mais visualizados (API gratuita)
        """
        try:
            from datetime import date, timedelta
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y/%m/%d')
            
            url = f'https://wikimedia.org/api/rest_v1/metrics/pageviews/top/pt.wikipedia/all-access/{yesterday}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for item in data['items'][0]['articles'][:5]:
                    article_title = item['article']
                    articles.append({
                        'url': f'https://pt.wikipedia.org/wiki/{article_title}',
                        'title': article_title.replace('_', ' '),
                        'source': 'Wikipedia Trending',
                        'content': f'Tópico em alta na Wikipedia: {article_title}',
                        'published_date': datetime.now()
                    })
                
                return articles
        except Exception as e:
            print(f"Erro ao buscar Wikipedia Trending: {e}")
            return []
    
    # ==========================================
    # INTEGRAÇÃO COM O CONTENT ROBOT
    # ==========================================
    def get_all_sources(self, niche='finance') -> Dict[str, List[Dict]]:
        """
        Retorna todas as fontes de uma vez (com tratamento de erros)
        """
        sources = {}
        
        # Currents API
        try:
            currents_data = self.fetch_currents_api()
            sources['currents'] = currents_data if currents_data else []
        except Exception as e:
            print(f"Erro em Currents: {e}")
            sources['currents'] = []
        
        # GNews
        try:
            gnews_data = self.fetch_gnews()
            sources['gnews'] = gnews_data if gnews_data else []
        except Exception as e:
            print(f"Erro em GNews: {e}")
            sources['gnews'] = []
        
        # Medium
        try:
            medium_data = self.fetch_medium_topic(niche)
            sources['medium'] = medium_data if medium_data else []
        except Exception as e:
            print(f"Erro em Medium: {e}")
            sources['medium'] = []
        
        # Dev.to
        try:
            devto_data = self.fetch_devto_articles() if niche == 'tech' else []
            sources['devto'] = devto_data if devto_data else []
        except Exception as e:
            print(f"Erro em Dev.to: {e}")
            sources['devto'] = []
        
        # Hacker News
        try:
            hn_data = self.fetch_hackernews_top()
            sources['hackernews'] = hn_data if hn_data else []
        except Exception as e:
            print(f"Erro em Hacker News: {e}")
            sources['hackernews'] = []
        
        # Wikipedia
        try:
            wiki_data = self.fetch_wikipedia_trending()
            sources['wikipedia'] = wiki_data if wiki_data else []
        except Exception as e:
            print(f"Erro em Wikipedia: {e}")
            sources['wikipedia'] = []
        
        return sources


# ==========================================
# EXEMPLO DE USO
# ==========================================
if __name__ == '__main__':
    manager = AdvancedSourcesManager()
    
    print("🔍 Testando fontes de conteúdo...\n")
    
    # Teste todas as fontes
    sources = manager.get_all_sources(niche='finance')
    
    for source_name, articles in sources.items():
        print(f"\n📰 {source_name.upper()}:")
        print(f"   Encontrados: {len(articles)} artigos")
        
        if articles:
            print(f"   Exemplo: {articles[0]['title'][:60]}...")
    
    print("\n✅ Teste concluído!")
    print("\n💡 DICA: Adicione estas fontes ao seu content_robot.py:")
    print("   1. Adicione as API keys no .env")
    print("   2. Importe: from sources_manager import AdvancedSourcesManager")
    print("   3. Use no run_cycle() para coletar mais artigos!")