# -*- coding: utf-8 -*-
import json
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StrategicGoal(models.Model):
    _name = "strategic.goal"
    _description = "Strategic Goal"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, id desc"

    name = fields.Char(
        string="Nome da Meta",
        required=True,
        tracking=True,
        help="Nome oficial da meta estratégica."
    )
    code = fields.Char(
        string="Código",
        tracking=True,
        help="Código interno único para identificação da meta."
    )

    description = fields.Html(
        string="Descrição da Meta",
        help="Descrição detalhada da meta, seu contexto e propósito estratégico."
    )

    deliverable_description = fields.Html(
        string="Descrição do Entregável",
        help="Descreva claramente o entregável esperado para esta meta."
    )

    charter_html = fields.Html(
        string="Charter da Meta",
        help="Charter formal da meta, incluindo escopo, critérios, responsabilidades e expectativas."
    )

    active = fields.Boolean(string="Ativo", default=True, tracking=True)

    area_id = fields.Many2one(
        "strategic.area",
        string="Área Estratégica",
        required=True,
        ondelete="restrict",
        tracking=True,
        help="Área estratégica à qual esta meta pertence."
    )

    company_id = fields.Many2one(
        "res.company",
        string="Companhia",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
        help="Companhia à qual esta meta pertence."
    )

    manager_ids = fields.Many2many(
        "hr.employee",
        "strategic_goal_manager_rel",
        "goal_id",
        "employee_id",
        string="Gestores Específicos",
        tracking=True,
        help="Gestores específicos desta meta. Por padrão herda os gestores da área."
    )

    viewer_ids = fields.Many2many(
        "res.users",
        "strategic_goal_viewer_rel",
        "goal_id",
        "user_id",
        string="Visualizadores",
        help="Utilizadores que podem visualizar a meta. Por padrão herda os visualizadores da área."
    )

    responsible_id = fields.Many2one(
        "hr.employee",
        string="Responsável Principal",
        tracking=True,
        help="Responsável principal da meta. Por padrão será o responsável da área estratégica."
    )

    assignment_ids = fields.One2many(
        "strategic.goal.assignment",
        "goal_id",
        string="Atribuições",
    )

    employee_ids = fields.Many2many(
        "hr.employee",
        compute="_compute_employee_ids",
        string="Funcionários",
        help="Funcionários atribuídos a esta meta."
    )

    periodicity = fields.Selection([
        ("weekly", "Semanal"),
        ("monthly", "Mensal"),
        ("quarterly", "Trimestral"),
        ("yearly", "Anual"),
    ], string="Periodicidade", required=True, default="monthly", tracking=True, help="Periodicidade esperada dos relatórios.")

    metric_type = fields.Selection([
        ("absolute", "Valor Absoluto"),
        ("percentage", "Percentagem"),
        ("boolean", "Sim/Não"),
        ("scale", "Escala"),
        ("monetary", "Monetário"),
        ("time", "Tempo"),
        ("deliverables", "Quantidade de Entregáveis"),
    ], string="Tipo de Indicador", required=True, default="absolute", tracking=True, help="Tipo principal de medição da meta.")

    metric_description = fields.Html(
        string="Descrição da Medição",
        help="Explique como a medição será feita, critérios, fontes e interpretação do indicador."
    )
    specific_metric_ids = fields.One2many(
        "strategic.goal.metric.line",
        "goal_id",
        string="Métricas Específicas",
        help="Métricas específicas configuradas uma única vez na meta e replicadas automaticamente nos relatórios."
    )

    target_value = fields.Float(
        string="Valor Alvo",
        tracking=True,
        help="Valor objetivo esperado para o indicador."
    )

    min_expected_value = fields.Float(
        string="Valor Mínimo Esperado",
        help="Valor mínimo aceitável para considerar a meta sob controlo."
    )

    unit_of_measure = fields.Char(
        string="Unidade de Medida",
        help="Unidade utilizada no indicador, por exemplo %, horas, tarefas, MZN."
    )

    weight = fields.Float(
        string="Peso",
        default=1.0,
        help="Peso relativo da meta dentro do conjunto estratégico."
    )

    priority = fields.Selection([
        ("0", "Baixa"),
        ("1", "Normal"),
        ("2", "Alta"),
        ("3", "Crítica"),
    ], string="Prioridade", default="1", tracking=True, help="Prioridade operacional e estratégica da meta.")

    criticality = fields.Selection([
        ("low", "Baixa"),
        ("medium", "Média"),
        ("high", "Alta"),
        ("critical", "Crítica"),
    ], string="Criticidade", default="medium", tracking=True, help="Nível de criticidade da meta.")

    start_date = fields.Date(
        string="Data de Início",
        required=True,
        default=fields.Date.context_today,
        help="Data de início da validade da meta."
    )

    end_date = fields.Date(
        string="Data de Fim",
        help="Data de fim da validade da meta."
    )

    report_count = fields.Integer(
        string="Total de Relatórios",
        compute="_compute_report_count",
    )

    ai_metadata_json = fields.Text(
        string="AI Metadata JSON",
        help="Estrutura JSON preparada para consumo analítico e futuro uso por agentes inteligentes."
    )

    @api.depends("assignment_ids", "assignment_ids.employee_id", "assignment_ids.active")
    def _compute_employee_ids(self):
        for record in self:
            employee_ids = record.sudo().assignment_ids.filtered(lambda a: a.active).mapped("employee_id").ids
            record.employee_ids = [(6, 0, employee_ids)]

    def _compute_report_count(self):
        report_model = self.env["job.report"]
        for record in self:
            record.report_count = report_model.search_count([
                ("goal_id", "=", record.id)
            ])

    @api.onchange("area_id")
    def _onchange_area_id(self):
        for record in self:
            if record.area_id:
                record.company_id = record.area_id.company_id.id
                area = record.area_id.sudo()
                if not record.sudo().manager_ids.ids:
                    record.manager_ids = [(6, 0, area.manager_ids.ids)]
                if not record.viewer_ids:
                    record.viewer_ids = [(6, 0, area.viewer_ids.ids)]
                if not record.responsible_id:
                    record.responsible_id = area.responsible_id.id

    @api.model
    def create(self, vals):
        if vals.get("area_id"):
            area = self.env["strategic.area"].sudo().browse(vals["area_id"])
            if area:
                if not vals.get("manager_ids") and area.manager_ids:
                    vals["manager_ids"] = [(6, 0, area.manager_ids.ids)]
                if not vals.get("viewer_ids") and area.viewer_ids:
                    vals["viewer_ids"] = [(6, 0, area.viewer_ids.ids)]
                if not vals.get("responsible_id") and area.responsible_id:
                    vals["responsible_id"] = area.responsible_id.id
                if not vals.get("company_id"):
                    vals["company_id"] = area.company_id.id
        record = super(StrategicGoal, self).create(vals)
        return record

    def write(self, vals):
        if vals.get("area_id"):
            area = self.env["strategic.area"].sudo().browse(vals["area_id"])
            if area:
                if "company_id" not in vals:
                    vals["company_id"] = area.company_id.id
                if "responsible_id" not in vals and area.responsible_id:
                    vals["responsible_id"] = area.responsible_id.id
        return super(StrategicGoal, self).write(vals)

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError(_("A data final não pode ser inferior à data inicial."))

    @api.constrains("target_value", "min_expected_value")
    def _check_target_values(self):
        for record in self:
            if (
                record.target_value
                and record.min_expected_value
                and record.min_expected_value > record.target_value
            ):
                raise ValidationError(_("O valor mínimo esperado não pode ser superior ao valor alvo."))

    def _get_period_range(self, periodicity, reference_date=False):
        reference_date = reference_date or fields.Date.context_today(self)

        if periodicity == "weekly":
            start = reference_date - timedelta(days=reference_date.weekday())
            end = start + timedelta(days=6)

        elif periodicity == "monthly":
            start = reference_date.replace(day=1)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)

        elif periodicity == "quarterly":
            quarter = ((reference_date.month - 1) // 3) + 1
            start_month = (quarter - 1) * 3 + 1
            start = reference_date.replace(month=start_month, day=1)
            if start_month == 10:
                end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = start.replace(month=start_month + 3, day=1) - timedelta(days=1)

        else:
            start = reference_date.replace(month=1, day=1)
            end = reference_date.replace(month=12, day=31)

        return start, end

    def _build_ai_payload(self, assignment, period_start, period_end):
        payload = {
            "company": self.company_id.name or "",
            "area": self.area_id.name or "",
            "goal": self.name or "",
            "goal_code": self.code or "",
            "periodicity": self.periodicity or "",
            "employee": assignment.employee_id.name or "",
            "manager": assignment.manager_id.name if assignment.manager_id else "",
            "period_start": str(period_start),
            "period_end": str(period_end),
            "metric_type": self.metric_type or "",
            "target_value": self.target_value or 0.0,
            "unit_of_measure": self.unit_of_measure or "",
            "criticality": self.criticality or "",
        }
        return payload

    def _prepare_report_vals(self, assignment, period_start, period_end):
        report_model = self.env["job.report"]
        manual_exists = report_model.search_count([
            ("goal_id", "=", self.id),
            ("employee_id", "=", assignment.employee_id.id),
            ("period_start", "=", period_start),
            ("period_end", "=", period_end),
            ("is_manual", "=", True),
            ("status", "!=", "cancelled"),
        ])
        if manual_exists:
            return False

        return {
            "name": self.env["ir.sequence"].next_by_code("jstech.job.report") or _("Novo"),
            "goal_id": self.id,
            "area_id": self.area_id.id,
            "company_id": self.company_id.id,
            "employee_id": assignment.employee_id.id,
            "assignment_id": assignment.id,
            "manager_id": assignment.manager_id.id or self.responsible_id.id or False,
            "period_start": period_start,
            "period_end": period_end,
            "deadline_date": period_end,
            "status": "pending",
            "planned_value": self.target_value,
            "metric_type": self.metric_type,
            "unit_of_measure": self.unit_of_measure,
            "is_manual": False,
            "ai_metadata_json": json.dumps(
                self._build_ai_payload(assignment, period_start, period_end),
                ensure_ascii=False,
                indent=2
            ),
        }

    @api.model
    def _cron_generate_reports(self):
        today = fields.Date.context_today(self)
        goals = self.search([
            ("active", "=", True),
            ("start_date", "<=", today),
            "|",
            ("end_date", "=", False),
            ("end_date", ">=", today),
        ])

        report_model = self.env["job.report"]

        for goal in goals:
            period_start, period_end = goal._get_period_range(goal.periodicity, today)
            active_assignments = goal.assignment_ids.filtered(lambda a: a.active)

            for assignment in active_assignments:
                exists = report_model.search_count([
                    ("goal_id", "=", goal.id),
                    ("employee_id", "=", assignment.employee_id.id),
                    ("period_start", "=", period_start),
                    ("period_end", "=", period_end),
                    ("status", "!=", "cancelled"),
                ])
                if not exists:
                    vals = goal._prepare_report_vals(assignment, period_start, period_end)
                    if vals:
                        report_model.create(vals)


class StrategicGoalMetricLine(models.Model):
    _name = "strategic.goal.metric.line"
    _description = "Métrica Específica da Meta"
    _order = "sequence, id"

    sequence = fields.Integer(
        string="Sequência",
        default=10,
    )

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

    metric_name = fields.Char(
        string="Indicador",
        required=True,
        help="Nome do indicador específico que será avaliado no relatório."
    )

    metric_code = fields.Char(
        string="Código",
        help="Código interno do indicador."
    )

    description = fields.Html(
        string="Descrição",
        help="Descrição detalhada da métrica, sua finalidade, critérios e forma de medição."
    )

    metric_type = fields.Selection([
        ("absolute", "Valor Absoluto"),
        ("percentage", "Percentagem"),
        ("boolean", "Sim/Não"),
        ("scale", "Escala"),
        ("monetary", "Monetário"),
        ("time", "Tempo"),
        ("deliverables", "Quantidade de Entregáveis"),
    ], string="Tipo de Indicador", default="absolute", required=True)

    unit_of_measure = fields.Char(
        string="Unidade de Medida",
        help="Unidade utilizada para medir este indicador."
    )

    planned_value = fields.Float(
        string="Valor Planeado",
        help="Valor esperado desta métrica para cada relatório gerado."
    )

    weight = fields.Float(
        string="Peso",
        default=1.0,
        help="Peso desta métrica no acompanhamento da meta."
    )

    required = fields.Boolean(
        string="Obrigatória",
        default=True,
        help="Define se esta métrica deve ser preenchida no relatório."
    )

    active = fields.Boolean(
        string="Ativo",
        default=True,
    )
