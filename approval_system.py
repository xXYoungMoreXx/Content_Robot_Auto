"""
Sistema de Aprovação Manual de Artigos - CORRIGIDO v1.1
Revise artigos antes de publicar via interface web
"""
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
from typing import Dict, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import logging

Base = declarative_base()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PendingArticle(Base):
    """Artigos aguardando aprovação"""
    __tablename__ = 'pending_articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    meta_description = Column(Text)
    content = Column(Text)
    keywords = Column(Text)  # JSON array
    category = Column(String(100))
    source_url = Column(String(500))
    source_name = Column(String(200))
    
    quality_score = Column(Integer)
    originality_score = Column(Integer)
    seo_score = Column(Integer)
    
    status = Column(String(20), default='pending')  # pending, approved, rejected
    reviewed_at = Column(DateTime)
    reviewer_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.now)

app = Flask(__name__)

# CORREÇÃO CRÍTICA: Configuração CORS adequada
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configuração do banco
engine = create_engine('sqlite:///content_robot.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ==========================================
# ROTAS DA API
# ==========================================

@app.route('/')
def index():
    """Interface de aprovação de artigos"""
    return render_template_string(APPROVAL_HTML)

@app.route('/api/pending-articles')
def get_pending_articles():
    """Lista artigos pendentes"""
    session = Session()
    
    try:
        articles = session.query(PendingArticle).filter_by(
            status='pending'
        ).order_by(PendingArticle.created_at.desc()).all()
        
        logger.info(f"📋 Retornando {len(articles)} artigos pendentes")
        
        return jsonify([{
            'id': article.id,
            'title': article.title,
            'meta_description': article.meta_description,
            'content': article.content,
            'keywords': json.loads(article.keywords) if article.keywords else [],
            'category': article.category,
            'source_url': article.source_url,
            'source_name': article.source_name,
            'quality_score': article.quality_score,
            'originality_score': article.originality_score,
            'seo_score': article.seo_score,
            'created_at': article.created_at.strftime('%Y-%m-%d %H:%M')
        } for article in articles])
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar artigos: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/approve/<int:article_id>', methods=['POST', 'OPTIONS'])
def approve_article(article_id):
    """Aprova um artigo"""
    if request.method == 'OPTIONS':
        return '', 204
    
    session = Session()
    
    try:
        data = request.json or {}
        article = session.query(PendingArticle).get(article_id)
        
        if not article:
            return jsonify({'error': 'Artigo não encontrado'}), 404
        
        logger.info(f"✅ Aprovando artigo #{article_id}: {article.title[:50]}")
        
        article.status = 'approved'
        article.reviewed_at = datetime.now()
        article.reviewer_notes = data.get('notes', '')
        
        session.commit()
        
        # Publica no WordPress
        success = publish_to_wordpress(article)
        
        if success:
            logger.info(f"✅ Artigo #{article_id} publicado no WordPress")
            return jsonify({'message': 'Artigo aprovado e publicado!', 'success': True})
        else:
            logger.error(f"❌ Erro ao publicar artigo #{article_id} no WordPress")
            return jsonify({'message': 'Artigo aprovado mas erro ao publicar', 'success': False})
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Erro ao aprovar artigo: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/reject/<int:article_id>', methods=['POST', 'OPTIONS'])
def reject_article(article_id):
    """Rejeita um artigo"""
    if request.method == 'OPTIONS':
        return '', 204
    
    session = Session()
    
    try:
        data = request.json or {}
        article = session.query(PendingArticle).get(article_id)
        
        if not article:
            return jsonify({'error': 'Artigo não encontrado'}), 404
        
        logger.info(f"❌ Rejeitando artigo #{article_id}: {article.title[:50]}")
        
        article.status = 'rejected'
        article.reviewed_at = datetime.now()
        article.reviewer_notes = data.get('notes', '')
        
        session.commit()
        
        return jsonify({'message': 'Artigo rejeitado', 'success': True})
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Erro ao rejeitar artigo: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/stats')
def get_stats():
    """Estatísticas do sistema"""
    session = Session()
    
    try:
        pending = session.query(PendingArticle).filter_by(status='pending').count()
        approved = session.query(PendingArticle).filter_by(status='approved').count()
        rejected = session.query(PendingArticle).filter_by(status='rejected').count()
        
        return jsonify({
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'total': pending + approved + rejected
        })
        
    finally:
        session.close()

# ==========================================
# INTEGRAÇÃO COM WORDPRESS
# ==========================================

def publish_to_wordpress(article: PendingArticle) -> bool:
    """Publica artigo aprovado no WordPress"""
    from dotenv import load_dotenv
    load_dotenv()
    
    wp_url = os.getenv('WORDPRESS_URL')
    wp_user = os.getenv('WORDPRESS_USERNAME')
    wp_pass = os.getenv('WORDPRESS_PASSWORD')
    
    if not all([wp_url, wp_user, wp_pass]):
        logger.error("❌ WordPress não configurado no .env")
        return False
    
    try:
        logger.info(f"📤 Publicando no WordPress: {article.title[:50]}...")
        
        post_data = {
            'title': article.title,
            'content': article.content,
            'excerpt': article.meta_description,
            'status': 'publish',  # Publica diretamente
            'categories': [1],  # Ajuste conforme necessário
        }
        
        response = requests.post(
            f'{wp_url}/wp-json/wp/v2/posts',
            auth=(wp_user, wp_pass),
            json=post_data,
            timeout=45
        )
        
        if response.status_code in [200, 201]:
            post_url = response.json().get('link')
            logger.info(f"✅ Publicado: {post_url}")
            return True
        else:
            logger.error(f"❌ WordPress erro {response.status_code}: {response.text[:200]}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Erro ao publicar: {e}")
        return False

# ==========================================
# HTML DA INTERFACE - CORRIGIDO
# ==========================================

APPROVAL_HTML = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Aprovação - Content Robot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        
        .header h1 {
            font-size: 2em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .stats {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 20px;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 15px 30px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .article-card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .article-title {
            font-size: 1.8em;
            margin-bottom: 15px;
            color: #333;
        }
        
        .article-meta {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .score-badge {
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .score-excellent { background: #d4edda; color: #155724; }
        .score-good { background: #cce5ff; color: #004085; }
        .score-fair { background: #fff3cd; color: #856404; }
        
        .article-description {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            font-style: italic;
        }
        
        .article-content {
            line-height: 1.8;
            color: #333;
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 15px;
            background: #fafafa;
            border-radius: 10px;
        }
        
        .article-keywords {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        
        .keyword-tag {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 15px;
            font-size: 0.85em;
        }
        
        .action-buttons {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        
        .btn {
            padding: 12px 30px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-approve {
            background: #28a745;
            color: white;
        }
        
        .btn-reject {
            background: #dc3545;
            color: white;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .empty-state h2 {
            font-size: 2em;
            margin-bottom: 10px;
            color: #28a745;
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error-state {
            text-align: center;
            padding: 60px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            color: #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✏️ Sistema de Aprovação de Artigos</h1>
            <p>Revise e aprove artigos antes da publicação</p>
            
            <div class="stats" id="statsContainer">
                <div class="stat-card">
                    <div class="stat-number" id="pendingCount">-</div>
                    <div class="stat-label">Pendentes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="approvedCount">-</div>
                    <div class="stat-label">Aprovados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="rejectedCount">-</div>
                    <div class="stat-label">Rejeitados</div>
                </div>
            </div>
        </div>
        
        <div id="articlesContainer">
            <div class="loading">
                <div class="loading-spinner"></div>
                <p>🔄 Carregando artigos...</p>
            </div>
        </div>
    </div>
    
    <script>
        let isLoading = false;
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                document.getElementById('pendingCount').textContent = stats.pending;
                document.getElementById('approvedCount').textContent = stats.approved;
                document.getElementById('rejectedCount').textContent = stats.rejected;
            } catch (error) {
                console.error('Erro ao carregar estatísticas:', error);
            }
        }
        
        async function loadArticles() {
            if (isLoading) return;
            isLoading = true;
            
            try {
                console.log('📡 Buscando artigos pendentes...');
                
                const response = await fetch('/api/pending-articles', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const articles = await response.json();
                console.log(`✅ ${articles.length} artigos carregados`);
                
                const container = document.getElementById('articlesContainer');
                
                if (articles.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <h2>✅ Tudo revisado!</h2>
                            <p>Não há artigos pendentes de aprovação no momento.</p>
                            <p style="margin-top: 10px; color: #666;">
                                A página atualiza automaticamente a cada 30 segundos.
                            </p>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = articles.map(article => {
                    const qualityClass = article.quality_score >= 90 ? 'score-excellent' : 
                                       article.quality_score >= 75 ? 'score-good' : 'score-fair';
                    
                    return `
                        <div class="article-card" id="article-${article.id}">
                            <h2 class="article-title">${escapeHtml(article.title)}</h2>
                            
                            <div class="article-meta">
                                <span class="score-badge ${qualityClass}">Qualidade: ${article.quality_score}/100</span>
                                <span class="score-badge ${qualityClass}">Originalidade: ${article.originality_score}/100</span>
                                <span class="score-badge ${qualityClass}">SEO: ${article.seo_score}/100</span>
                                <span style="color: #666;">📰 ${escapeHtml(article.source_name)}</span>
                                <span style="color: #666;">🕐 ${article.created_at}</span>
                            </div>
                            
                            <div class="article-description">
                                <strong>Meta Description:</strong> ${escapeHtml(article.meta_description)}
                            </div>
                            
                            <div class="article-keywords">
                                ${article.keywords.map(kw => `<span class="keyword-tag">${escapeHtml(kw)}</span>`).join('')}
                            </div>
                            
                            <div class="article-content">
                                ${article.content}
                            </div>
                            
                            <div class="action-buttons">
                                <button class="btn btn-reject" onclick="rejectArticle(${article.id})" id="reject-${article.id}">
                                    ❌ Rejeitar
                                </button>
                                <button class="btn btn-approve" onclick="approveArticle(${article.id})" id="approve-${article.id}">
                                    ✅ Aprovar & Publicar
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
                
            } catch (error) {
                console.error('❌ Erro ao carregar artigos:', error);
                document.getElementById('articlesContainer').innerHTML = `
                    <div class="error-state">
                        <h2>❌ Erro ao Carregar</h2>
                        <p>${error.message}</p>
                        <p style="margin-top: 20px;">
                            <button class="btn" onclick="loadArticles()" style="background: #667eea; color: white;">
                                🔄 Tentar Novamente
                            </button>
                        </p>
                    </div>
                `;
            } finally {
                isLoading = false;
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function approveArticle(id) {
            if (!confirm('Tem certeza que deseja APROVAR e PUBLICAR este artigo?')) return;
            
            const approveBtn = document.getElementById(`approve-${id}`);
            const rejectBtn = document.getElementById(`reject-${id}`);
            
            approveBtn.disabled = true;
            rejectBtn.disabled = true;
            approveBtn.textContent = '⏳ Publicando...';
            
            try {
                const notes = prompt('Notas de revisão (opcional):') || '';
                
                const response = await fetch(`/api/approve/${id}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({notes})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ Artigo aprovado e publicado com sucesso!');
                    document.getElementById(`article-${id}`).remove();
                    await loadStats();
                    await loadArticles();
                } else {
                    alert('⚠️ ' + result.message);
                    approveBtn.disabled = false;
                    rejectBtn.disabled = false;
                    approveBtn.textContent = '✅ Aprovar & Publicar';
                }
            } catch (error) {
                alert('❌ Erro ao aprovar artigo: ' + error.message);
                approveBtn.disabled = false;
                rejectBtn.disabled = false;
                approveBtn.textContent = '✅ Aprovar & Publicar';
            }
        }
        
        async function rejectArticle(id) {
            if (!confirm('Tem certeza que deseja REJEITAR este artigo?')) return;
            
            const approveBtn = document.getElementById(`approve-${id}`);
            const rejectBtn = document.getElementById(`reject-${id}`);
            
            approveBtn.disabled = true;
            rejectBtn.disabled = true;
            rejectBtn.textContent = '⏳ Rejeitando...';
            
            try {
                const notes = prompt('Motivo da rejeição:') || '';
                
                const response = await fetch(`/api/reject/${id}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({notes})
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ Artigo rejeitado');
                    document.getElementById(`article-${id}`).remove();
                    await loadStats();
                    await loadArticles();
                }
            } catch (error) {
                alert('❌ Erro ao rejeitar artigo: ' + error.message);
                approveBtn.disabled = false;
                rejectBtn.disabled = false;
                rejectBtn.textContent = '❌ Rejeitar';
            }
        }
        
        // Carrega artigos e estatísticas ao iniciar
        loadArticles();
        loadStats();
        
        // Atualiza a cada 30 segundos
        setInterval(() => {
            loadArticles();
            loadStats();
        }, 30000);
    </script>
</body>
</html>
'''

# ==========================================
# INTEGRAÇÃO COM CONTENT ROBOT
# ==========================================

def save_for_approval(article_data: Dict) -> int:
    """
    Salva artigo para aprovação manual
    Retorna ID do artigo pendente
    """
    session = Session()
    
    try:
        pending = PendingArticle(
            title=article_data['titulo'],
            meta_description=article_data['meta_description'],
            content=article_data['conteudo_completo'],
            keywords=json.dumps(article_data.get('palavras_chave', []), ensure_ascii=False),
            category=article_data.get('categoria', 'Notícias'),
            source_url=article_data.get('source_url', ''),
            source_name=article_data.get('source_name', ''),
            quality_score=article_data.get('qualidade_score', 0),
            originality_score=article_data.get('originalidade_score', 0),
            seo_score=article_data.get('seo_score', 0)
        )
        
        session.add(pending)
        session.commit()
        
        article_id = pending.id
        
        logger.info(f"✅ Artigo #{article_id} salvo para aprovação: {article_data['titulo'][:50]}")
        
        return article_id
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Erro ao salvar para aprovação: {e}")
        return 0
    finally:
        session.close()


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════╗
    ║   ✏️  SISTEMA DE APROVAÇÃO v1.1          ║
    ║                                          ║
    ║   🌐 Interface: http://localhost:5001    ║
    ║   🔄 Auto-refresh: 30 segundos           ║
    ║                                          ║
    ║   Pressione Ctrl+C para parar           ║
    ╚══════════════════════════════════════════╝
    """)
    
    app.run(debug=True, host='0.0.0.0', port=5001)