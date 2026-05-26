# -*- coding: utf-8 -*-
from odoo import fields, models


class JobReportSnapshot(models.Model):
    _name = "job.report.snapshot"
    _description = "Job Report Snapshot"
    _order = "snapshot_date desc, id desc"
    _rec_name = "report_id"

    report_id = fields.Many2one(
        "job.report",
        string="Relatório",
        required=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Companhia",
        required=True,
        index=True,
    )

    area_id = fields.Many2one(
        "strategic.area",
        string="Área",
        required=True,
        index=True,
    )

    goal_id = fields.Many2one(
        "strategic.goal",
        string="Meta",
        required=True,
        index=True,
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Funcionário",
        required=True,
        index=True,
    )

    manager_id = fields.Many2one(
        "hr.employee",
        string="Gestor",
        index=True,
    )

    snapshot_date = fields.Datetime(
        string="Data do Snapshot",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )

    status = fields.Selection([
        ("pending", "Pendente"),
        ("draft", "Em Elaboração"),
        ("submitted", "Submetido"),
        ("approved", "Aprovado"),
        ("rejected", "Rejeitado"),
        ("late", "Atrasado"),
        ("done", "Concluído"),
        ("cancelled", "Cancelado"),
    ], string="Estado", index=True)

    planned_value = fields.Float(string="Valor Planeado")
    actual_value = fields.Float(string="Valor Real")
    achievement_percentage = fields.Float(string="% Cumprimento")
    delay_days = fields.Integer(string="Dias de Atraso")
    final_score = fields.Float(string="Pontuação Final")

    performance_band = fields.Selection([
        ("critical", "Crítico"),
        ("low", "Baixo"),
        ("medium", "Médio"),
        ("high", "Alto"),
        ("excellent", "Excelente"),
    ], string="Faixa de Desempenho")

    risk_band = fields.Selection([
        ("low", "Baixo"),
        ("medium", "Médio"),
        ("high", "Alto"),
        ("critical", "Crítico"),
    ], string="Nível de Risco")

    submitted_on_time = fields.Boolean(string="Entregue no Prazo")
    anomaly_flag = fields.Boolean(string="Anomalia Detectada")