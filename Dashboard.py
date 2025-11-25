"""
Dashboard Web para Content Robot v3.1
Execute: python dashboard.py
Acesse: http://localhost:5000
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from content_robot import PublishedArticle, APIUsageLog, Base
import json

app = Flask(__name__)
CORS(app)

# Configuração do banco
engine = create_engine('sqlite:///content_robot.db')
Session = sessionmaker(bind=engine)

@app.route('/')
def index():
    """Página principal do dashboard"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Retorna estatísticas gerais"""
    session = Session()
    
    try:
        # Total de artigos
        total = session.query(PublishedArticle).count()
        
        # Últimos 7 dias
        last_7_days = session.query(PublishedArticle).filter(
            PublishedArticle.published_date >= datetime.now() - timedelta(days=7)
        ).count()
        
        # Hoje
        today = session.query(PublishedArticle).filter(
            PublishedArticle.published_date >= datetime.now().date()
        ).count()
        
        # Qualidade média
        avg_quality = session.query(func.avg(PublishedArticle.quality_score)).scalar() or 0
        avg_originality = session.query(func.avg(PublishedArticle.originality_score)).scalar() or 0
        
        # API usage hoje
        api_today = session.query(APIUsageLog).filter(
            APIUsageLog.date >= datetime.now().date()
        ).all()
        
        api_calls = sum(log.calls for log in api_today)
        api_tokens = sum(log.tokens_used for log in api_today)
        
        return jsonify({
            'total_articles': total,
            'today': today,
            'last_7_days': last_7_days,
            'avg_quality': round(avg_quality, 1),
            'avg_originality': round(avg_originality, 1),
            'api_calls_today': api_calls,
            'api_tokens_today': api_tokens
        })
        
    finally:
        session.close()

@app.route('/api/recent-articles')
def get_recent_articles():
    """Retorna últimos artigos publicados"""
    session = Session()
    
    try:
        articles = session.query(PublishedArticle).order_by(
            PublishedArticle.published_date.desc()
        ).limit(10).all()
        
        return jsonify([{
            'id': article.id,
            'title': article.title,
            'source': article.source,
            'published_date': article.published_date.strftime('%Y-%m-%d %H:%M'),
            'quality_score': article.quality_score,
            'originality_score': article.originality_score,
            'wordpress_url': article.wordpress_url
        } for article in articles])
        
    finally:
        session.close()

@app.route('/api/chart-data')
def get_chart_data():
    """Dados para gráficos"""
    session = Session()
    
    try:
        # Artigos por dia (últimos 7 dias)
        days = []
        counts = []
        
        for i in range(6, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            count = session.query(PublishedArticle).filter(
                func.date(PublishedArticle.published_date) == date
            ).count()
            
            days.append(date.strftime('%d/%m'))
            counts.append(count)
        
        # Distribuição de qualidade
        quality_ranges = {
            '90-100': 0,
            '80-89': 0,
            '70-79': 0,
            '60-69': 0,
            '<60': 0
        }
        
        articles = session.query(PublishedArticle.quality_score).all()
        for article in articles:
            score = article.quality_score or 0
            if score >= 90:
                quality_ranges['90-100'] += 1
            elif score >= 80:
                quality_ranges['80-89'] += 1
            elif score >= 70:
                quality_ranges['70-79'] += 1
            elif score >= 60:
                quality_ranges['60-69'] += 1
            else:
                quality_ranges['<60'] += 1
        
        return jsonify({
            'daily_articles': {
                'labels': days,
                'data': counts
            },
            'quality_distribution': {
                'labels': list(quality_ranges.keys()),
                'data': list(quality_ranges.values())
            }
        })
        
    finally:
        session.close()

@app.route('/api/logs')
def get_logs():
    """Retorna últimas linhas do log"""
    try:
        with open('robot.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_50 = lines[-50:]
            return jsonify({'logs': last_50})
    except Exception as e:
        return jsonify({'logs': [f'Erro ao ler logs: {str(e)}']})

@app.route('/api/system-info')
def get_system_info():
    """Informações do sistema"""
    import psutil
    
    return jsonify({
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('.').percent
    })

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════╗
    ║   🤖 CONTENT ROBOT DASHBOARD v3.1         ║
    ║                                            ║
    ║   📊 Dashboard: http://localhost:5000     ║
    ║   🔄 Auto-refresh: A cada 30 segundos     ║
    ║                                            ║
    ║   Pressione Ctrl+C para parar             ║
    ╚════════════════════════════════════════════╝
    """)
    
    app.run(debug=True, host='0.0.0.0', port=5000)