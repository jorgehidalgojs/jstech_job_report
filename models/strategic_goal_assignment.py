# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StrategicGoalAssignment(models.Model):
    _name = "strategic.goal.assignment"
    _description = "Strategic Goal Assignment"
    _order = "goal_id, employee_id"

    goal_id = fields.Many2one(
        "strategic.goal",
        string="Meta",
        required=True,
        ondelete="cascade",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Companhia",
        related="goal_id.company_id",
        store=True,
        readonly=True,
    )

    area_id = fields.Many2one(
        "strategic.area",
        string="Área",
        related="goal_id.area_id",
        store=True,
        readonly=True,
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Funcionário",
        required=True,
        ondelete="restrict",
    )

    manager_id = fields.Many2one(
        "hr.employee",
        string="Gestor Responsável",
        ondelete="restrict",
    )

    user_id = fields.Many2one(
        "res.users",
        string="Utilizador",
        related="employee_id.user_id",
        store=True,
        readonly=True,
    )

    active = fields.Boolean(string="Ativo", default=True)

    @api.constrains("goal_id", "employee_id")
    def _check_unique_assignment(self):
        for record in self:
            duplicate = self.search([
                ("id", "!=", record.id),
                ("goal_id", "=", record.goal_id.id),
                ("employee_id", "=", record.employee_id.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_("Este funcionário já está atribuído a esta meta."))