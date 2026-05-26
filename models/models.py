# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class StrategicArea(models.Model):
    _name = "estrategic.area"
    _description = "Área Estratégica"

    name = fields.Char(string="Nome", required=True)
    description = fields.Text(string="Descrição")
    active = fields.Boolean(string="Ativo", default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Companhia',
        required=True,
        default=lambda self: self.env.company
    )



class StrategicGoal(models.Model):
    _name = "estrategic.goal"
    _description = "Objetivo Estratégico"

    name = fields.Char(string="Nome", required=True)
    description = fields.Text(string="Descrição")
    area_id = fields.Many2one(
        comodel_name="estrategic.area",
        string="Área Estratégica",
        required=True
    )
    active = fields.Boolean(string="Ativo", default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Companhia',
        required=True,
        default=lambda self: self.env.company
    )


class JobReport(models.Model):
    _name = "job.report"
    _description = "Relatório de Trabalho"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Título", required=True, tracking=True)

    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Funcionário",
        required=True,
        default=lambda self: self._get_default_employee()
        ,tracking=True
    )
    date_start = fields.Date(string="Data Início", required=True)
    date_end = fields.Date(string="Data Fim", required=True)
    strategic_goal_id = fields.Many2one(
        comodel_name="estrategic.goal",
        string="Objetivo Estratégico",
        required=True,
        tracking=True
    )
    manager_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="relatorio_gestor_rel",
        column1="report_id",
        column2="manager_id",
        string="Gestores",
        tracking=True
    )

    is_manager = fields.Boolean(
        string="Es Gestor",
        compute="_compute_is_manager",
        store=False
    )

    @api.depends('manager_ids')
    def _compute_is_manager(self):
        for record in self:
            current_employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
            record.is_manager = current_employee and current_employee.id in record.sudo().manager_ids.ids

    summary = fields.Text(string="Resumo",tracking=True)
    task_ids = fields.Many2many(
        comodel_name="project.task",
        string="Tarefas Relacionadas",
        tracking=True
    )
    report_body = fields.Html(string="Relatório",tracking=True)
    status = fields.Selection(
        [
            ('draft', 'Rascunho'),
            ('submitted', 'Submetido'),
            ('approved', 'Aprovado'),
            ('rejected', 'Rejeitado'),
            ('cancelled', 'Cancelado'),
            ('done', 'Concluído')
        ],
        string="Status",
        default="draft",
        tracking=True
    )
    feedback = fields.Html(string="Feedback do Gestor",tracking=True)

    def write(self, vals):
        for record in self:
            if record.status in ['approved', 'cancelled', 'done'] and any(
                    field for field in vals if field not in ['status']):
                raise UserError(
                    "Não é possível modificar um Relatório de Trabalho que já está Aprovado, Cancelado ou Concluído.")
        return super(JobReport, self).write(vals)

    @api.model
    def _get_default_employee(self):
        """Devuelve el empleado asociado al usuario actual."""
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
        return employee.id if employee else False

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,tracking=True)

    def action_submit(self):
        self.status = 'submitted'

    def action_approve(self):
        self.status = 'approved'

    def action_reject(self):
        self.status = 'rejected'

    def action_cancel(self):
        self.status = 'cancelled'

    def action_done(self):
        self.status = 'done'

    @api.model
    def _get_report_base_filename(self):
        return 'relatorio_trabalho_' + str(self.name)

