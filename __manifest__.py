# -*- coding: utf-8 -*-
{
    "name": "Gestão de Desempenho",
    "summary": "Gestão estratégica de metas, relatórios periódicos e análise executiva com base preparada para Inteligência Artificial.",
    "description": """
Gestão de Desempenho Estratégico
================================

Módulo avançado para gestão estratégica e operacional do desempenho organizacional, concebido para empresas que pretendem melhorar o controlo, a execução e a análise dos seus objetivos.

Principais funcionalidades
--------------------------

• Gestão de Áreas Estratégicas com governação completa  
• Definição de Metas com indicadores, periodicidade e peso estratégico  
• Atribuição de Gestores, Visualizadores e Funcionários responsáveis  
• Geração automática de relatórios periódicos (sem duplicação)  
• Registo manual de relatórios com controlo inteligente  
• Avaliação quantitativa do desempenho e scoring automático  
• Trazabilidade completa (chatter, histórico e auditoria)  
• Dashboard executivo por Área e por Empresa  
• Estrutura multiempresa (multi-company)  
• Base preparada para integração com Inteligência Artificial  

Arquitetura preparada para:

• Mineração de dados  
• Machine Learning  
• Agentes de Inteligência Artificial  
• Análise preditiva de desempenho  

---

Desenvolvido por  
Direção de Tecnologia e Inovação  
Grupo Palace  

Autor  
Jorge Hidalgo Ruiz  

Suporte  
helpdesk@palace.co.mz  

Website  
https://helpdesk.palace.co.mz  
    """,
    "version": "15.0.2.0.0",
    "category": "Produtividade",
    "author": "Jorge Hidalgo Ruiz",
    "website": "https://helpdesk.palace.co.mz",
    "support": "helpdesk@palace.co.mz",
    "license": "LGPL-3",

    "depends": [
        "base",
        "mail",
        "hr",
        "project",
        "web",
    ],

    "data": [
        # Segurança
        "security/job_report_security.xml",
        "security/ir.model.access.csv",

        # Dados
        "data/ir_sequence_data.xml",
        "data/job_report_cron.xml",

        # Ações
        "views/actions.xml",

        # Views principais
        "views/strategic_area_views.xml",
        "views/strategic_goal_views.xml",
        "views/strategic_goal_assignment_views.xml",
        "views/job_report_views.xml",
        "views/dashboard_views.xml",
        "views/menus.xml",

        # Relatórios
        "report/job_report_report.xml",
        "report/job_report_templates.xml",
    ],

    "assets": {
        "web.assets_backend": [
            "jstech_job_report/static/src/css/dashboard.css",
        ],
    },

    "application": True,
    "installable": True,
    "auto_install": False,
}
