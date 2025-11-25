"""
Sistema de Otimização de Prompts A/B Testing
Teste diferentes prompts e escolha o melhor automaticamente
"""
import json
from datetime import datetime
from typing import Dict, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class PromptTest(Base):
    """Armazena resultados de testes A/B de prompts"""
    __tablename__ = 'prompt_tests'
    
    id = Column(Integer, primary_key=True)
    prompt_id = Column(String(50), index=True)
    prompt_name = Column(String(200))
    prompt_content = Column(Text)
    
    # Métricas
    total_uses = Column(Integer, default=0)
    avg_quality_score = Column(Float, default=0)
    avg_originality_score = Column(Float, default=0)
    avg_seo_score = Column(Float, default=0)
    success_rate = Column(Float, default=0)  # % de artigos aceitos
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PromptOptimizer:
    """Gerencia testes A/B de prompts"""
    
    def __init__(self):
        engine = create_engine('sqlite:///content_robot.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
        # Carregar prompts de teste
        self.prompts = self._load_prompts()
        self.current_prompt_index = 0
    
    def _load_prompts(self) -> Dict[str, str]:
        """Carrega biblioteca de prompts para teste"""
        return {
            # ==========================================
            # PROMPT 1: JORNALÍSTICO FORMAL
            # ==========================================
            'prompt_jornalistico': """
Você é um jornalista econômico premiado escrevendo para investidores profissionais.

ESTILO: Formal, investigativo, baseado em dados.
TOM: Neutro, imparcial, analítico.

ESTRUTURA OBRIGATÓRIA:
1. Lead impactante (quem, o quê, quando, onde, por quê)
2. Contexto e antecedentes
3. Análise de especialistas
4. Dados e estatísticas
5. Projeções fundamentadas

REGRAS:
- ZERO opinião pessoal
- Sempre citar fontes originais
- Usar números e métricas concretas
- Linguagem técnica mas acessível
- Mínimo 1000 palavras

ARTIGO ORIGINAL:
Título: {article_title}
Fonte: {article_source}
Conteúdo: {article_content}

Retorne JSON:
{{
    "titulo": "...",
    "meta_description": "...",
    "conteudo_completo": "<h2>...</h2><p>...</p>",
    "palavras_chave": ["..."],
    "categoria": "...",
    "qualidade_score": 0,
    "originalidade_score": 0,
    "seo_score": 0
}}
""",

            # ==========================================
            # PROMPT 2: CASUAL E ACESSÍVEL
            # ==========================================
            'prompt_casual': """
Você é um criador de conteúdo que simplifica finanças para o público geral.

ESTILO: Conversacional, storytelling, didático.
TOM: Amigável, empolgante, próximo.

ESTRUTURA:
1. Hook irresistível (história ou pergunta)
2. Explicação simples do conceito
3. Exemplos práticos do dia a dia
4. Dicas acionáveis
5. Conclusão motivadora

REGRAS:
- Use analogias e metáforas
- Explique jargões técnicos
- Inclua exemplos brasileiros
- Tom de conversa com amigo
- 800-1000 palavras

ARTIGO ORIGINAL:
Título: {article_title}
Fonte: {article_source}
Conteúdo: {article_content}

Retorne JSON:
{{
    "titulo": "...",
    "meta_description": "...",
    "conteudo_completo": "<h2>...</h2><p>...</p>",
    "palavras_chave": ["..."],
    "categoria": "...",
    "qualidade_score": 0,
    "originalidade_score": 0,
    "seo_score": 0
}}
""",

            # ==========================================
            # PROMPT 3: CLICKBAIT EDUCATIVO
            # ==========================================
            'prompt_viral': """
Você é um growth hacker de conteúdo que cria artigos virais mas informativos.

ESTILO: Chamativo, dinâmico, envolvente.
TOM: Curioso, urgente, revelador.

ESTRUTURA:
1. Título ULTRA chamativo (curiosidade + benefício)
2. Abertura com gancho emocional
3. Listas e bullets (fácil escaneamento)
4. Surpresas e revelações
5. CTA forte no final

REGRAS:
- Títulos com números e adjetivos fortes
- Promessas realistas mas empolgantes
- Subtítulos que contam uma história
- Formatação visual rica (listas, destaques)
- 700-900 palavras

ARTIGO ORIGINAL:
Título: {article_title}
Fonte: {article_source}
Conteúdo: {article_content}

Retorne JSON:
{{
    "titulo": "...",
    "meta_description": "...",
    "conteudo_completo": "<h2>...</h2><p>...</p>",
    "palavras_chave": ["..."],
    "categoria": "...",
    "qualidade_score": 0,
    "originalidade_score": 0,
    "seo_score": 0
}}
""",

            # ==========================================
            # PROMPT 4: SEO MÁXIMO
            # ==========================================
            'prompt_seo_beast': """
Você é um especialista em SEO que cria conteúdo otimizado para ranquear no Google.

ESTILO: Estruturado, rico em palavras-chave, completo.
TOM: Autoritativo, confiável, referencial.

ESTRUTURA SEO:
1. H1 com palavra-chave principal
2. Introdução com long-tail keywords
3. H2 para cada subtópico (com keywords)
4. FAQ section (People Also Ask)
5. Conclusão com keywords semânticas

REGRAS SEO:
- Densidade de palavra-chave: 1-2%
- LSI keywords naturalmente distribuídas
- Meta description com CTA
- Internal linking opportunities (mencione)
- Schema markup friendly
- 1200+ palavras

ARTIGO ORIGINAL:
Título: {article_title}
Fonte: {article_source}
Conteúdo: {article_content}

Retorne JSON:
{{
    "titulo": "...",
    "meta_description": "...",
    "conteudo_completo": "<h2>...</h2><p>...</p>",
    "palavras_chave": ["..."],
    "categoria": "...",
    "qualidade_score": 0,
    "originalidade_score": 0,
    "seo_score": 0
}}
""",

            # ==========================================
            # PROMPT 5: ANÁLISE PROFUNDA
            # ==========================================
            'prompt_analise_profunda': """
Você é um analista financeiro certificado que escreve relatórios aprofundados.

ESTILO: Técnico, detalhado, fundamentado.
TOM: Profissional, preciso, criterioso.

ESTRUTURA:
1. Executive Summary
2. Análise Quantitativa (números, gráficos mentais)
3. Análise Qualitativa (tendências, sentimento)
4. Comparação de Mercado (benchmarks)
5. Riscos e Oportunidades
6. Recomendações Estratégicas

REGRAS:
- Cite estudos e relatórios
- Use terminologia técnica correta
- Apresente múltiplos cenários
- Inclua disclaimers apropriados
- 1500+ palavras

ARTIGO ORIGINAL:
Título: {article_title}
Fonte: {article_source}
Conteúdo: {article_content}

Retorne JSON:
{{
    "titulo": "...",
    "meta_description": "...",
    "conteudo_completo": "<h2>...</h2><p>...</p>",
    "palavras_chave": ["..."],
    "categoria": "...",
    "qualidade_score": 0,
    "originalidade_score": 0,
    "seo_score": 0
}}
"""
        }
    
    def get_next_prompt(self) -> tuple[str, str]:
        """
        Retorna próximo prompt para teste (round-robin)
        """
        prompt_ids = list(self.prompts.keys())
        prompt_id = prompt_ids[self.current_prompt_index % len(prompt_ids)]
        prompt_content = self.prompts[prompt_id]
        
        self.current_prompt_index += 1
        
        return prompt_id, prompt_content
    
    def record_result(self, prompt_id: str, quality_score: float, 
                     originality_score: float, seo_score: float, 
                     was_accepted: bool):
        """
        Registra resultado de um teste
        """
        try:
            test = self.session.query(PromptTest).filter_by(prompt_id=prompt_id).first()
            
            if not test:
                test = PromptTest(
                    prompt_id=prompt_id,
                    prompt_name=prompt_id.replace('prompt_', '').title(),
                    prompt_content=self.prompts[prompt_id]
                )
                self.session.add(test)
            
            # Atualiza métricas (média móvel)
            n = test.total_uses
            test.avg_quality_score = ((test.avg_quality_score * n) + quality_score) / (n + 1)
            test.avg_originality_score = ((test.avg_originality_score * n) + originality_score) / (n + 1)
            test.avg_seo_score = ((test.avg_seo_score * n) + seo_score) / (n + 1)
            test.success_rate = ((test.success_rate * n) + (1 if was_accepted else 0)) / (n + 1)
            test.total_uses += 1
            
            self.session.commit()
            
            print(f"✅ Resultado registrado para {prompt_id}")
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ Erro ao registrar resultado: {e}")
    
    def get_best_prompt(self) -> tuple[str, str]:
        """
        Retorna o prompt com melhor performance
        """
        tests = self.session.query(PromptTest).filter(
            PromptTest.total_uses >= 5  # Mínimo de testes
        ).order_by(
            (PromptTest.avg_quality_score + 
             PromptTest.avg_originality_score + 
             PromptTest.avg_seo_score + 
             (PromptTest.success_rate * 100)).desc()
        ).first()
        
        if tests:
            return tests.prompt_id, tests.prompt_content
        
        # Fallback: retorna o primeiro
        return list(self.prompts.items())[0]
    
    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas de todos os prompts
        """
        tests = self.session.query(PromptTest).all()
        
        stats = []
        for test in tests:
            stats.append({
                'name': test.prompt_name,
                'uses': test.total_uses,
                'quality': round(test.avg_quality_score, 1),
                'originality': round(test.avg_originality_score, 1),
                'seo': round(test.avg_seo_score, 1),
                'success_rate': round(test.success_rate * 100, 1),
                'total_score': round(
                    (test.avg_quality_score + test.avg_originality_score + 
                     test.avg_seo_score) / 3, 1
                )
            })
        
        return sorted(stats, key=lambda x: x['total_score'], reverse=True)


# ==========================================
# INTEGRAÇÃO COM CONTENT ROBOT
# ==========================================
def integrate_with_robot():
    """
    Instruções para integrar com o content_robot.py
    """
    integration_code = '''
# No content_robot.py, adicione no __init__:
from prompt_optimizer import PromptOptimizer

class ContentRobot:
    def __init__(self, config: Dict):
        # ... código existente ...
        
        # Adicione isto:
        self.prompt_optimizer = PromptOptimizer()
        self.use_ab_testing = config.get('use_prompt_ab_testing', False)
    
    def process_with_gemini(self, article: ArticleData) -> Optional[Dict]:
        # Substitua a linha de prompt por:
        
        if self.use_ab_testing:
            prompt_id, prompt_template = self.prompt_optimizer.get_next_prompt()
        else:
            prompt_id = 'custom'
            prompt_template = self.config.get('custom_prompt') or DEFAULT_PROMPT
        
        prompt = prompt_template.format(
            article_title=article.title,
            article_source=article.source,
            article_content=article.content[:4000]
        )
        
        # ... resto do código ...
        
        # Após obter o resultado, registre:
        if self.use_ab_testing and result:
            self.prompt_optimizer.record_result(
                prompt_id=prompt_id,
                quality_score=result.get('qualidade_score', 0),
                originality_score=result.get('originalidade_score', 0),
                seo_score=result.get('seo_score', 0),
                was_accepted=True  # ou False se foi rejeitado
            )
        
        return result

# No config do main(), adicione:
config = {
    'use_prompt_ab_testing': True,  # Ativa A/B testing
    # ... resto da config ...
}
'''
    
    print(integration_code)


# ==========================================
# EXEMPLO DE USO
# ==========================================
if __name__ == '__main__':
    optimizer = PromptOptimizer()
    
    print("🧪 SISTEMA DE A/B TESTING DE PROMPTS\n")
    print("=" * 50)
    
    # Mostra prompts disponíveis
    print("\n📝 Prompts Disponíveis:")
    for i, prompt_id in enumerate(optimizer.prompts.keys(), 1):
        name = prompt_id.replace('prompt_', '').replace('_', ' ').title()
        print(f"   {i}. {name}")
    
    # Mostra estatísticas
    stats = optimizer.get_statistics()
    
    if stats:
        print("\n📊 Estatísticas de Performance:")
        print(f"\n{'Nome':<20} {'Usos':<8} {'Qualidade':<10} {'Original':<10} {'SEO':<8} {'Taxa Sucesso':<12} {'Score Total'}")
        print("-" * 90)
        
        for stat in stats:
            print(f"{stat['name']:<20} {stat['uses']:<8} {stat['quality']:<10} "
                  f"{stat['originality']:<10} {stat['seo']:<8} "
                  f"{stat['success_rate']}%{' ':<8} {stat['total_score']}")
    else:
        print("\n⚠️ Nenhum teste executado ainda.")
        print("   Execute o robô com 'use_prompt_ab_testing: True' no config!")
    
    print("\n" + "=" * 50)
    print("\n💡 Para integrar com o robô, execute:")
    print("   python prompt_optimizer.py")
    print("   E siga as instruções de integração.\n")