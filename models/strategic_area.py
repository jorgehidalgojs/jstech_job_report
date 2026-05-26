# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StrategicArea(models.Model):
    _name = "strategic.area"
    _description = "Strategic Area"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    name = fields.Char(string="Nome da Área", required=True, tracking=True, help="Nome oficial da área estratégica.")
    code = fields.Char(string="Código", tracking=True, help="Código interno único para identificação da área.")
    description = fields.Html(string="Descrição", help="Descrição estratégica detalhada da área.")
    charter_html = fields.Html(
        string="Charter da Área",
        help="Charter formal da área, incluindo missão, escopo, objetivos, responsabilidades e diretrizes."
    )

    active = fields.Boolean(string="Ativo", default=True, tracking=True)
    sequence = fields.Integer(string="Sequência", default=10, help="Define a ordem de apresentação da área.")
    color = fields.Integer(string="Cor")

    company_id = fields.Many2one(
        "res.company",
        string="Companhia",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
        help="Companhia à qual esta área pertence."
    )

    manager_ids = fields.Many2many(
        "hr.employee",
        "strategic_area_manager_rel",
        "area_id",
        "employee_id",
        string="Gestores da Área",
        tracking=True,
        help="Gestores principais responsáveis por esta área."
    )

    viewer_ids = fields.Many2many(
        "res.users",
        "strategic_area_viewer_rel",
        "area_id",
        "user_id",
        string="Visualizadores",
        help="Utilizadores com permissão de consulta sobre esta área."
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        "strategic_area_employee_rel",
        "area_id",
        "employee_id",
        string="Funcionários",
        help="Funcionários associados à área."
    )

    responsible_id = fields.Many2one(
        "hr.employee",
        string="Responsável Principal",
        compute="_compute_responsible_id",
        store=True,
        readonly=False,
        help="Responsável principal da área. Por padrão será o primeiro gestor definido."
    )

    goal_ids = fields.One2many(
        "strategic.goal",
        "area_id",
        string="Metas",
    )

    goal_count = fields.Integer(
        string="Total de Metas",
        compute="_compute_goal_count",
    )

    report_count = fields.Integer(
        string="Total de Relatórios",
        compute="_compute_report_count",
    )

    @api.depends("manager_ids")
    def _compute_responsible_id(self):
        for record in self:
            manager_ids = record.sudo().manager_ids.ids
            record.responsible_id = manager_ids[0] if manager_ids else False

    @api.onchange("manager_ids")
    def _onchange_manager_ids(self):
        for record in self:
            manager_ids = record.sudo().manager_ids.ids
            if manager_ids and (not record.responsible_id or record.responsible_id.id not in manager_ids):
                record.responsible_id = manager_ids[0]

    def _compute_goal_count(self):
        for record in self:
            record.goal_count = len(record.goal_ids)

    def _compute_report_count(self):
        report_model = self.env["job.report"]
        for record in self:
            record.report_count = report_model.search_count([
                ("area_id", "=", record.id)
            ])
