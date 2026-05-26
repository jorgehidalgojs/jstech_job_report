# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class JobReportMetricLine(models.Model):
    _name = "job.report.metric.line"
    _description = "Job Report Metric Line"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    report_id = fields.Many2one(
        "job.report",
        string="Relatório",
        required=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Companhia",
        related="report_id.company_id",
        store=True,
        readonly=True,
    )

    metric_name = fields.Char(
        string="Indicador",
        required=True,
    )

    metric_code = fields.Char(string="Código")
    description = fields.Text(string="Descrição")

    metric_type = fields.Selection([
        ("absolute", "Valor Absoluto"),
        ("percentage", "Percentagem"),
        ("boolean", "Sim/Não"),
        ("scale", "Escala"),
        ("monetary", "Monetário"),
        ("time", "Tempo"),
        ("deliverables", "Quantidade de Entregáveis"),
    ], string="Tipo", default="absolute", required=True)

    unit_of_measure = fields.Char(string="Unidade")
    planned_value = fields.Float(string="Valor Planeado")
    actual_value = fields.Float(string="Valor Real")
    achievement_percentage = fields.Float(
        string="% Cumprimento",
        compute="_compute_achievement",
        store=True,
    )

    weight = fields.Float(string="Peso", default=1.0)
    score = fields.Float(
        string="Pontuação",
        compute="_compute_score",
        store=True,
    )

    notes = fields.Text(string="Observações")

    @api.depends("planned_value", "actual_value")
    def _compute_achievement(self):
        for record in self:
            if record.planned_value:
                record.achievement_percentage = (record.actual_value / record.planned_value) * 100.0
            else:
                record.achievement_percentage = 0.0

    @api.depends("achievement_percentage", "weight")
    def _compute_score(self):
        for record in self:
            achievement = min(max(record.achievement_percentage or 0.0, 0.0), 100.0)
            record.score = achievement * (record.weight or 1.0)

    @api.constrains("weight")
    def _check_weight(self):
        for record in self:
            if record.weight < 0:
                raise ValidationError(_("O peso não pode ser negativo."))