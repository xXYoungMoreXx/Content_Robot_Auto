"""
Sistema de Analytics e Relatórios
Robô de Conteúdo v3.0

Gera relatórios detalhados de performance

Execução:
python analytics.py [periodo]

Exemplos:
python analytics.py daily
python analytics.py weekly
python analytics.py monthly
python analytics.py full
"""

import sys
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json

class ContentAnalytics:
    def __init__(self, db_path='content_robot.db'):
        self.db_path = db_path
        
        if not Path(db_path).exists():
            # Tenta banco alternativo
            if Path('published_articles.db').exists():
                self.db_path = 'published_articles.db'
            else:
                raise FileNotFoundError(f"Banco de dados não encontrado: {db_path}")
        
        self.conn = sqlite3.connect(self.db_path)
        self.df = self._load_data()
    
    def _load_data(self):
        """Carrega dados do banco"""
        query = """
        SELECT 
            id,
            hash,
            url,
            title,
            source,
            published_date,
            quality_score,
            originality_score,
            wordpress_url,
            LENGTH(full_content) as content_length
        FROM published_articles
        ORDER BY published_date DESC
        """
        
        df = pd.read_sql_query(query, self.conn)
        df['published_date'] = pd.to_datetime(df['published_date'])
        return df
    
    def get_period_data(self, period='daily'):
        """Filtra dados por período"""
        now = datetime.now()
        
        period_map = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'full': None
        }
        
        days = period_map.get(period, 7)
        
        if days:
            cutoff = now - timedelta(days=days)
            return self.df[self.df['published_date'] >= cutoff]
        
        return self.df
    
    def general_metrics(self, period_df):
        """Métricas gerais"""
        return {
            'total_articles': len(period_df),
            'avg_quality': period_df['quality_score'].mean(),
            'avg_originality': period_df['originality_score'].mean(),
            'avg_length': period_df['content_length'].mean(),
            'median_quality': period_df['quality_score'].median(),
            'std_quality': period_df['quality_score'].std(),
            'min_quality': period_df['quality_score'].min(),
            'max_quality': period_df['quality_score'].max()
        }
    
    def source_performance(self, period_df):
        """Performance por fonte"""
        source_stats = period_df.groupby('source').agg({
            'id': 'count',
            'quality_score': ['mean', 'std'],
            'originality_score': 'mean',
            'content_length': 'mean'
        }).round(2)
        
        source_stats.columns = ['total', 'avg_quality', 'std_quality', 'avg_originality', 'avg_length']
        source_stats = source_stats.sort_values('total', ascending=False)
        
        return source_stats
    
    def temporal_analysis(self, period_df):
        """Análise temporal"""
        # Artigos por dia
        daily = period_df.groupby(period_df['published_date'].dt.date).size()
        
        # Artigos por hora do dia
        hourly = period_df.groupby(period_df['published_date'].dt.hour).size()
        
        # Artigos por dia da semana
        weekly = period_df.groupby(period_df['published_date'].dt.day_name()).size()
        
        return {
            'daily_avg': daily.mean(),
            'daily_std': daily.std(),
            'best_hour': hourly.idxmax() if not hourly.empty else None,
            'best_day': weekly.idxmax() if not weekly.empty else None,
            'worst_day': weekly.idxmin() if not weekly.empty else None
        }
    
    def quality_distribution(self, period_df):
        """Distribuição de qualidade"""
        bins = [0, 50, 70, 85, 95, 100]
        labels = ['Baixa (<50)', 'Média (50-70)', 'Boa (70-85)', 'Ótima (85-95)', 'Excelente (95-100)']
        
        period_df['quality_category'] = pd.cut(period_df['quality_score'], bins=bins, labels=labels)
        distribution = period_df['quality_category'].value_counts()
        
        return distribution
    
    def top_articles(self, period_df, n=10):
        """Top N artigos"""
        top_quality = period_df.nlargest(n, 'quality_score')[['title', 'source', 'quality_score', 'published_date']]
        top_original = period_df.nlargest(n, 'originality_score')[['title', 'source', 'originality_score', 'published_date']]
        
        return {
            'top_quality': top_quality,
            'top_originality': top_original
        }
    
    def growth_analysis(self, period_df):
        """Análise de crescimento"""
        if len(period_df) < 14:
            return None
        
        # Divide em duas metades
        mid_point = len(period_df) // 2
        first_half = period_df.iloc[:mid_point]
        second_half = period_df.iloc[mid_point:]
        
        # Calcula crescimento
        growth_rate = ((len(second_half) - len(first_half)) / len(first_half) * 100)
        quality_change = second_half['quality_score'].mean() - first_half['quality_score'].mean()
        
        return {
            'articles_growth': growth_rate,
            'quality_change': quality_change,
            'first_half_avg': len(first_half) / (len(first_half) / len(period_df)),
            'second_half_avg': len(second_half) / (len(second_half) / len(period_df))
        }
    
    def recommendations(self, period_df, source_stats):
        """Gera recomendações automáticas"""
        recommendations = []
        
        # 1. Fontes de baixa qualidade
        low_quality_sources = source_stats[source_stats['avg_quality'] < 70]
        if not low_quality_sources.empty:
            recommendations.append({
                'type': 'warning',
                'category': 'Fontes',
                'message': f"{len(low_quality_sources)} fonte(s) com qualidade < 70",
                'action': f"Considere remover: {', '.join(low_quality_sources.index.tolist()[:3])}"
            })
        
        # 2. Fontes de alta qualidade
        high_quality_sources = source_stats[source_stats['avg_quality'] >= 90]
        if not high_quality_sources.empty:
            recommendations.append({
                'type': 'success',
                'category': 'Fontes',
                'message': f"{len(high_quality_sources)} fonte(s) excelente(s)",
                'action': f"Priorize: {', '.join(high_quality_sources.index.tolist()[:3])}"
            })
        
        # 3. Volume de produção
        daily_avg = len(period_df) / max((period_df['published_date'].max() - period_df['published_date'].min()).days, 1)
        if daily_avg < 5:
            recommendations.append({
                'type': 'info',
                'category': 'Volume',
                'message': f"Média de {daily_avg:.1f} artigos/dia (baixo)",
                'action': "Adicione mais fontes RSS ou reduza qualidade mínima"
            })
        elif daily_avg > 30:
            recommendations.append({
                'type': 'info',
                'category': 'Volume',
                'message': f"Média de {daily_avg:.1f} artigos/dia (alto)",
                'action': "Considere aumentar qualidade mínima ou remover fontes"
            })
        
        # 4. Qualidade geral
        avg_quality = period_df['quality_score'].mean()
        if avg_quality < 75:
            recommendations.append({
                'type': 'warning',
                'category': 'Qualidade',
                'message': f"Qualidade média de {avg_quality:.1f} (abaixo do ideal)",
                'action': "Aumente min_quality_score ou melhore prompt da IA"
            })
        
        # 5. Consistência
        quality_std = period_df['quality_score'].std()
        if quality_std > 15:
            recommendations.append({
                'type': 'info',
                'category': 'Consistência',
                'message': f"Alta variação na qualidade (std: {quality_std:.1f})",
                'action': "Revise configurações de fontes e qualidade mínima"
            })
        
        return recommendations
    
    def generate_report(self, period='weekly'):
        """Gera relatório completo"""
        print("="*80)
        print(f"📊 RELATÓRIO DE ANALYTICS - ROBÔ DE CONTEÚDO v3.0")
        print("="*80)
        print(f"Período: {period.upper()}")
        print(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Banco de dados: {self.db_path}")
        print("="*80)
        
        # Carrega dados do período
        period_df = self.get_period_data(period)
        
        if period_df.empty:
            print("\n❌ Nenhum dado encontrado para o período selecionado.")
            return
        
        print(f"\n📅 Dados do período: {len(period_df)} artigos")
        print(f"   De: {period_df['published_date'].min().strftime('%d/%m/%Y')}")
        print(f"   Até: {period_df['published_date'].max().strftime('%d/%m/%Y')}")
        
        # 1. Métricas Gerais
        print("\n" + "="*80)
        print("📊 MÉTRICAS GERAIS")
        print("="*80)
        
        metrics = self.general_metrics(period_df)
        print(f"\nTotal de artigos: {metrics['total_articles']}")
        print(f"Qualidade média: {metrics['avg_quality']:.1f}/100")
        print(f"Originalidade média: {metrics['avg_originality']:.1f}/100")
        print(f"Tamanho médio: {metrics['avg_length']:,.0f} caracteres")
        print(f"\nDistribuição de qualidade:")
        print(f"   Mínima: {metrics['min_quality']:.1f}")
        print(f"   Mediana: {metrics['median_quality']:.1f}")
        print(f"   Média: {metrics['avg_quality']:.1f}")
        print(f"   Máxima: {metrics['max_quality']:.1f}")
        print(f"   Desvio padrão: {metrics['std_quality']:.1f}")
        
        # 2. Performance por Fonte
        print("\n" + "="*80)
        print("🏆 PERFORMANCE POR FONTE")
        print("="*80)
        
        source_stats = self.source_performance(period_df)
        print(f"\nTop 10 fontes mais produtivas:")
        print(source_stats.head(10).to_string())
        
        # 3. Análise Temporal
        print("\n" + "="*80)
        print("⏰ ANÁLISE TEMPORAL")
        print("="*80)
        
        temporal = self.temporal_analysis(period_df)
        print(f"\nMédia diária: {temporal['daily_avg']:.1f} artigos/dia")
        print(f"Desvio padrão diário: {temporal['daily_std']:.1f}")
        if temporal['best_hour']:
            print(f"Melhor hora: {temporal['best_hour']}:00")
        if temporal['best_day']:
            print(f"Melhor dia da semana: {temporal['best_day']}")
        if temporal['worst_day']:
            print(f"Pior dia da semana: {temporal['worst_day']}")
        
        # 4. Distribuição de Qualidade
        print("\n" + "="*80)
        print("📈 DISTRIBUIÇÃO DE QUALIDADE")
        print("="*80)
        
        distribution = self.quality_distribution(period_df)
        print("\n" + distribution.to_string())
        
        # 5. Top Artigos
        print("\n" + "="*80)
        print("⭐ TOP 5 ARTIGOS")
        print("="*80)
        
        top = self.top_articles(period_df, 5)
        
        print("\n🏆 Maior Qualidade:")
        for idx, row in top['top_quality'].iterrows():
            print(f"   {row['quality_score']:.1f} | {row['title'][:60]}...")
        
        print("\n✨ Maior Originalidade:")
        for idx, row in top['top_originality'].iterrows():
            print(f"   {row['originality_score']:.1f} | {row['title'][:60]}...")
        
        # 6. Análise de Crescimento
        if period != 'daily':
            print("\n" + "="*80)
            print("📈 ANÁLISE DE CRESCIMENTO")
            print("="*80)
            
            growth = self.growth_analysis(period_df)
            if growth:
                print(f"\nCrescimento de artigos: {growth['articles_growth']:+.1f}%")
                print(f"Mudança na qualidade: {growth['quality_change']:+.1f} pontos")
        
        # 7. Recomendações
        print("\n" + "="*80)
        print("💡 RECOMENDAÇÕES AUTOMÁTICAS")
        print("="*80)
        
        recommendations = self.recommendations(period_df, source_stats)
        
        if not recommendations:
            print("\n✅ Tudo funcionando perfeitamente! Sem recomendações.")
        else:
            for rec in recommendations:
                icon = {'warning': '⚠️', 'success': '✅', 'info': 'ℹ️'}[rec['type']]
                print(f"\n{icon} {rec['category']}: {rec['message']}")
                print(f"   → Ação: {rec['action']}")
        
        # 8. Exportar dados
        print("\n" + "="*80)
        print("💾 EXPORTAR RELATÓRIO")
        print("="*80)
        
        export_filename = f"analytics_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'metadata': {
                'period': period,
                'generated_at': datetime.now().isoformat(),
                'database': self.db_path,
                'total_articles': len(period_df)
            },
            'metrics': metrics,
            'source_performance': source_stats.to_dict(),
            'temporal_analysis': temporal,
            'quality_distribution': distribution.to_dict(),
            'recommendations': recommendations
        }
        
        with open(export_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n✅ Relatório exportado: {export_filename}")
        
        print("\n" + "="*80)
        print("✅ RELATÓRIO CONCLUÍDO")
        print("="*80)
    
    def close(self):
        """Fecha conexão com banco"""
        self.conn.close()

def main():
    """Função principal"""
    # Determina período
    if len(sys.argv) > 1:
        period = sys.argv[1].lower()
    else:
        print("Períodos disponíveis: daily, weekly, monthly, quarterly, full")
        period = input("Escolha um período (padrão: weekly): ").strip().lower()
        if not period:
            period = 'weekly'
    
    valid_periods = ['daily', 'weekly', 'monthly', 'quarterly', 'full']
    if period not in valid_periods:
        print(f"❌ Período inválido. Use: {', '.join(valid_periods)}")
        return
    
    try:
        analytics = ContentAnalytics()
        analytics.generate_report(period)
        analytics.close()
    except FileNotFoundError as e:
        print(f"❌ Erro: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()