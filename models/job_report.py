# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext


class JobReport(models.Model):
    _name = "job.report"
    _description = "Job Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "period_end desc, id desc"
    _rec_name = "name"

    name = fields.Char(
        string="Referência",
        required=True,
        copy=False,
        default=lambda self: _("Novo"),
        tracking=True,
        help="Referência única do relatório."
    )

    active = fields.Boolean(default=True)

    is_manual = fields.Boolean(
        string="Criado Manualmente",
        default=True,
        tracking=True,
        help="Indica se o relatório foi criado manualmente pelo utilizador."
    )

    company_id = fields.Many2one(
        "res.company",
        string="Companhia",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
        help="Companhia à qual este relatório pertence."
    )

    area_id = fields.Many2one(
        "strategic.area",
        string="Área Estratégica",
        required=True,
        ondelete="restrict",
        tracking=True,
        help="Área estratégica relacionada com o relatório."
    )

    goal_id = fields.Many2one(
        "strategic.goal",
        string="Meta",
        required=True,
        ondelete="restrict",
        tracking=True,
        help="Meta estratégica associada ao relatório."
    )

    assignment_id = fields.Many2one(
        "strategic.goal.assignment",
        string="Atribuição",
        ondelete="set null",
        tracking=True,
        help="Atribuição do funcionário à meta."
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Funcionário",
        required=True,
        ondelete="restrict",
        tracking=True,
        help="Funcionário responsável pelo relatório."
    )

    employee_user_id = fields.Many2one(
        "res.users",
        string="Utilizador do Funcionário",
        related="employee_id.user_id",
        store=True,
        readonly=True,
    )

    manager_id = fields.Many2one(
        "hr.employee",
        string="Gestor Responsável",
        ondelete="restrict",
        tracking=True,
        help="Gestor principal responsável pela validação do relatório."
    )

    manager_user_id = fields.Many2one(
        "res.users",
        string="Utilizador do Gestor",
        related="manager_id.user_id",
        store=True,
        readonly=True,
    )

    period_start = fields.Date(
        string="Início do Período",
        required=True,
        tracking=True,
        help="Data inicial do período de reporte."
    )

    period_end = fields.Date(
        string="Fim do Período",
        required=True,
        tracking=True,
        help="Data final do período de reporte."
    )

    deadline_date = fields.Date(
        string="Prazo de Entrega",
        required=True,
        tracking=True,
        help="Prazo limite para submissão do relatório."
    )

    submission_date = fields.Datetime(
        string="Data de Submissão",
        tracking=True,
        readonly=True,
    )

    approved_date = fields.Datetime(
        string="Data de Aprovação",
        tracking=True,
        readonly=True,
    )

    rejected_date = fields.Datetime(
        string="Data de Rejeição",
        tracking=True,
        readonly=True,
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
    ], string="Estado", default="pending", required=True, tracking=True, index=True)

    summary = fields.Html(
        string="Resumo Executivo",
        help="Resumo executivo do período."
    )

    report_html = fields.Html(
        string="Relatório Detalhado",
        help="Relatório detalhado das atividades executadas."
    )

    deliverables_done = fields.Html(
        string="Entregáveis Realizados",
        help="Descreva os entregáveis realizados durante o período."
    )

    obstacles = fields.Html(
        string="Obstáculos",
        help="Registe bloqueios, riscos ou dificuldades encontradas."
    )

    corrective_actions = fields.Html(
        string="Ações Corretivas",
        help="Descreva as ações corretivas aplicadas ou propostas."
    )

    manager_feedback = fields.Html(
        string="Feedback do Gestor",
        help="Feedback formal do gestor sobre o relatório."
    )

    rejection_reason = fields.Html(
        string="Motivo da Rejeição",
        help="Motivo formal para rejeição do relatório."
    )

    task_ids = fields.Many2many(
        "project.task",
        "job_report_project_task_rel",
        "report_id",
        "task_id",
        string="Tarefas Relacionadas",
        help="Tarefas relacionadas com este relatório."
    )

    metric_line_ids = fields.One2many(
        "job.report.metric.line",
        "report_id",
        string="Métricas",
    )

    metric_count = fields.Integer(
        string="Total de Métricas",
        compute="_compute_metric_count",
    )

    snapshot_ids = fields.One2many(
        "job.report.snapshot",
        "report_id",
        string="Snapshots Analíticos",
    )

    periodicity = fields.Selection(
        related="goal_id.periodicity",
        string="Periodicidade",
        store=True,
        readonly=True,
    )

    metric_type = fields.Selection(
        related="goal_id.metric_type",
        string="Tipo de Indicador",
        store=True,
        readonly=True,
    )

    unit_of_measure = fields.Char(
        string="Unidade de Medida",
        tracking=True,
        help="Unidade utilizada nas medições do relatório."
    )

    planned_value = fields.Float(
        string="Valor Planeado",
        tracking=True,
        help="Valor previsto para o período."
    )

    actual_value = fields.Float(
        string="Valor Real",
        tracking=True,
        help="Valor efetivamente alcançado no período."
    )

    achievement_percentage = fields.Float(
        string="% Cumprimento",
        compute="_compute_scores",
        store=True,
    )

    deviation_value = fields.Float(
        string="Desvio",
        compute="_compute_scores",
        store=True,
    )

    submitted_on_time = fields.Boolean(
        string="Entregue no Prazo",
        compute="_compute_timeliness",
        store=True,
    )

    delay_days = fields.Integer(
        string="Dias de Atraso",
        compute="_compute_timeliness",
        store=True,
    )

    manager_score = fields.Float(
        string="Pontuação do Gestor",
        tracking=True,
        help="Pontuação atribuída pelo gestor."
    )

    quality_score = fields.Float(
        string="Pontuação de Qualidade",
        compute="_compute_scores",
        store=True,
    )

    final_score = fields.Float(
        string="Pontuação Final",
        compute="_compute_scores",
        store=True,
    )

    performance_band = fields.Selection([
        ("critical", "Crítico"),
        ("low", "Baixo"),
        ("medium", "Médio"),
        ("high", "Alto"),
        ("excellent", "Excelente"),
    ], string="Faixa de Desempenho", compute="_compute_scores", store=True)

    risk_band = fields.Selection([
        ("low", "Baixo"),
        ("medium", "Médio"),
        ("high", "Alto"),
        ("critical", "Crítico"),
    ], string="Nível de Risco", compute="_compute_timeliness", store=True)

    completeness_score = fields.Float(
        string="Pontuação de Completude",
        compute="_compute_completeness_score",
        store=True,
    )

    consistency_score = fields.Float(
        string="Pontuação de Consistência",
        compute="_compute_consistency_score",
        store=True,
    )

    timeliness_status = fields.Selection([
        ("on_time", "No Prazo"),
        ("late", "Atrasado"),
        ("not_submitted", "Não Submetido"),
    ], string="Estado Temporal", compute="_compute_timeliness", store=True)

    anomaly_flag = fields.Boolean(
        string="Anomalia Detectada",
        compute="_compute_anomaly_flag",
        store=True,
    )

    needs_review_flag = fields.Boolean(
        string="Requer Revisão",
        compute="_compute_needs_review_flag",
        store=True,
    )

    ai_metadata_json = fields.Text(
        string="AI Metadata JSON",
        tracking=False,
    )

    can_edit = fields.Boolean(
        string="Pode Editar",
        compute="_compute_user_permissions",
    )

    can_submit = fields.Boolean(
        string="Pode Submeter",
        compute="_compute_user_permissions",
    )

    can_approve = fields.Boolean(
        string="Pode Aprovar",
        compute="_compute_user_permissions",
    )

    can_reject = fields.Boolean(
        string="Pode Rejeitar",
        compute="_compute_user_permissions",
    )

    can_cancel = fields.Boolean(
        string="Pode Cancelar",
        compute="_compute_user_permissions",
    )

    can_done = fields.Boolean(
        string="Pode Concluir",
        compute="_compute_user_permissions",
    )

    available_area_ids = fields.Many2many(
        "strategic.area",
        compute="_compute_available_area_ids",
        string="Áreas Disponíveis"
    )

    available_goal_ids = fields.Many2many(
        "strategic.goal",
        compute="_compute_available_goal_ids",
        string="Metas Disponíveis"
    )

    ai_insight_html = fields.Html(
        string="Insight Inteligente",
        compute="_compute_ai_insights",
        store=True,
    )

    ai_recommendation_html = fields.Html(
        string="Recomendação Inteligente",
        compute="_compute_ai_insights",
        store=True,
    )

    executive_status = fields.Selection([
        ("excellent", "Excelente"),
        ("controlled", "Controlado"),
        ("attention", "Atenção"),
        ("critical", "Crítico"),
    ], string="Estado Executivo", compute="_compute_ai_insights", store=True)

    @api.depends("metric_line_ids")
    def _compute_metric_count(self):
        for record in self:
            record.metric_count = len(record.metric_line_ids)

    @api.depends("planned_value", "actual_value", "manager_score")
    def _compute_scores(self):
        for record in self:
            planned = record.planned_value or 0.0
            actual = record.actual_value or 0.0

            if planned > 0:
                achievement = (actual / planned) * 100.0
            else:
                achievement = 0.0

            deviation = actual - planned
            quality_score = min(max(achievement, 0.0), 100.0)
            manager_score = min(max(record.manager_score or 0.0, 0.0), 100.0)
            final_score = (quality_score * 0.70) + (manager_score * 0.30)

            if final_score < 40:
                band = "critical"
            elif final_score < 60:
                band = "low"
            elif final_score < 75:
                band = "medium"
            elif final_score < 90:
                band = "high"
            else:
                band = "excellent"

            record.achievement_percentage = achievement
            record.deviation_value = deviation
            record.quality_score = quality_score
            record.final_score = final_score
            record.performance_band = band

    @api.depends("deadline_date", "submission_date", "status")
    def _compute_timeliness(self):
        today = fields.Date.context_today(self)
        for record in self:
            delay_days = 0
            submitted_on_time = False
            timeliness_status = "not_submitted"

            if record.submission_date:
                submission_date = fields.Datetime.to_datetime(record.submission_date).date()
                if record.deadline_date and submission_date <= record.deadline_date:
                    submitted_on_time = True
                    timeliness_status = "on_time"
                elif record.deadline_date:
                    delay_days = (submission_date - record.deadline_date).days
                    timeliness_status = "late"
            else:
                if record.deadline_date and today > record.deadline_date and record.status not in ("approved", "done", "cancelled"):
                    delay_days = (today - record.deadline_date).days
                    timeliness_status = "late"

            if delay_days <= 0:
                risk_band = "low"
            elif delay_days <= 3:
                risk_band = "medium"
            elif delay_days <= 7:
                risk_band = "high"
            else:
                risk_band = "critical"

            record.submitted_on_time = submitted_on_time
            record.delay_days = delay_days
            record.timeliness_status = timeliness_status
            record.risk_band = risk_band

    @api.depends(
        "summary",
        "report_html",
        "deliverables_done",
        "obstacles",
        "corrective_actions",
        "actual_value",
    )
    def _compute_completeness_score(self):
        for record in self:
            score = 0.0
            if record.summary:
                score += 20.0
            if record.report_html:
                score += 25.0
            if record.deliverables_done:
                score += 20.0
            if record.obstacles:
                score += 10.0
            if record.corrective_actions:
                score += 10.0
            if record.actual_value:
                score += 15.0
            record.completeness_score = score

    @api.depends("achievement_percentage", "delay_days", "completeness_score")
    def _compute_consistency_score(self):
        for record in self:
            achievement = min(max(record.achievement_percentage or 0.0, 0.0), 100.0)
            completeness = min(max(record.completeness_score or 0.0, 0.0), 100.0)
            delay_penalty = min((record.delay_days or 0) * 5.0, 50.0)
            score = ((achievement * 0.5) + (completeness * 0.5)) - delay_penalty
            record.consistency_score = max(score, 0.0)

    @api.depends("achievement_percentage", "delay_days", "status")
    def _compute_anomaly_flag(self):
        for record in self:
            record.anomaly_flag = bool(
                (record.achievement_percentage and record.achievement_percentage < 40.0)
                or (record.delay_days and record.delay_days > 7)
                or record.status == "rejected"
            )

    @api.depends("anomaly_flag", "status", "completeness_score")
    def _compute_needs_review_flag(self):
        for record in self:
            record.needs_review_flag = bool(
                record.anomaly_flag
                or record.status in ("rejected", "late")
                or record.completeness_score < 50.0
            )

    def _get_current_employee(self):
        return self.env["hr.employee"].sudo().search([("user_id", "=", self.env.user.id)], limit=1)

    def _html_has_content(self, value):
        return bool((html2plaintext(value or "") or "").strip())

    def _format_field_names(self, field_names):
        labels = []
        for field_name in sorted(field_names):
            field = self._fields.get(field_name)
            labels.append(field.string if field else field_name)
        return ", ".join(labels)

    @api.depends("employee_id")
    def _compute_available_area_ids(self):
        current_employee = self._get_current_employee()
        area_model = self.env["strategic.area"]

        for record in self:
            if self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                record.available_area_ids = area_model.search([])
            elif current_employee:
                record.available_area_ids = area_model.search([
                    "|",
                    ("employee_ids", "in", current_employee.id),
                    ("goal_ids.assignment_ids.employee_id", "=", current_employee.id),
                ])
            else:
                record.available_area_ids = area_model.browse([])

    @api.depends("area_id", "employee_id")
    def _compute_available_goal_ids(self):
        current_employee = self._get_current_employee()
        goal_model = self.env["strategic.goal"]

        for record in self:
            domain = []
            if record.area_id:
                domain.append(("area_id", "=", record.area_id.id))

            if self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                record.available_goal_ids = goal_model.search(domain)
            elif current_employee:
                domain += [("assignment_ids.employee_id", "=", current_employee.id)]
                record.available_goal_ids = goal_model.search(domain)
            else:
                record.available_goal_ids = goal_model.browse([])

    def _compute_user_permissions(self):
        user = self.env.user
        employee = self.env["hr.employee"].sudo().search([("user_id", "=", user.id)], limit=1)
        employee_id = employee.id

        is_admin = user.has_group("jstech_job_report.group_job_report_admin")
        is_exec = user.has_group("jstech_job_report.group_executive_manager")
        is_area_manager = user.has_group("jstech_job_report.group_area_manager")
        is_goal_manager = user.has_group("jstech_job_report.group_goal_manager")

        for record in self:
            area_manager_ids = record.area_id.sudo().manager_ids.ids if record.area_id else []
            goal_manager_ids = record.goal_id.sudo().manager_ids.ids if record.goal_id else []

            is_owner = employee_id and record.employee_id.id == employee_id
            is_manager = employee_id and record.manager_id.id == employee_id
            is_area_mgr_for_record = employee_id and employee_id in area_manager_ids
            is_goal_mgr_for_record = employee_id and employee_id in goal_manager_ids
            can_review_record = bool(
                is_admin
                or is_exec
                or (is_area_manager and is_area_mgr_for_record)
                or ((is_goal_manager or is_manager) and (is_goal_mgr_for_record or is_manager))
            )

            record.can_edit = bool(
                is_admin
                or (is_owner and record.status in ("pending", "draft", "rejected", "late"))
            )

            record.can_submit = bool(
                is_admin
                or (is_owner and record.status in ("pending", "draft", "rejected", "late"))
            )

            record.can_approve = bool(
                record.status == "submitted" and can_review_record
            )

            record.can_reject = record.can_approve

            record.can_cancel = bool(
                is_admin and record.status not in ("approved", "done")
            )

            record.can_done = bool(
                record.status == "approved" and can_review_record
            )

    @api.depends(
        "final_score",
        "achievement_percentage",
        "delay_days",
        "status",
        "performance_band",
        "risk_band",
        "completeness_score",
        "consistency_score",
        "anomaly_flag",
        "needs_review_flag",
    )
    def _compute_ai_insights(self):
        for record in self:
            score = record.final_score or 0.0
            cumprimento = record.achievement_percentage or 0.0
            atraso = record.delay_days or 0

            if score >= 90 and cumprimento >= 90 and atraso == 0:
                executive_status = "excellent"
                insight = "O relatório apresenta desempenho excelente, com elevado cumprimento da meta e sem atrasos relevantes."
                recommendation = "Manter a estratégia atual, documentar boas práticas e replicar o modelo em outras metas ou áreas."

            elif score >= 75 and cumprimento >= 70 and atraso <= 3:
                executive_status = "controlled"
                insight = "O relatório encontra-se controlado, com desempenho positivo e pequenos desvios aceitáveis."
                recommendation = "Acompanhar a evolução nos próximos períodos e reforçar os pontos que contribuíram para o bom desempenho."

            elif score >= 50 or atraso <= 7:
                executive_status = "attention"
                insight = "O relatório requer atenção. Existem sinais de desvio no cumprimento, atraso ou qualidade da informação."
                recommendation = "Rever obstáculos, reforçar ações corretivas e acompanhar a meta com maior proximidade no próximo ciclo."

            else:
                executive_status = "critical"
                insight = "O relatório apresenta situação crítica, com baixo desempenho, atraso relevante ou risco elevado para a meta."
                recommendation = "Escalar para o gestor responsável, definir plano de recuperação e acompanhar semanalmente até estabilização."

            if record.status == "rejected":
                executive_status = "critical"
                insight = "O relatório foi rejeitado pelo gestor, indicando inconsistência, falta de informação ou desalinhamento com a meta."
                recommendation = "O funcionário deve rever o relatório, corrigir os pontos indicados e submeter novamente para validação."

            if record.status == "late":
                if executive_status != "critical":
                    executive_status = "attention"
                insight += " Existe atraso na entrega, o que pode afetar a leitura executiva do desempenho."
                recommendation += " Recomenda-se reforçar o controlo de prazos e alertas preventivos."

            record.executive_status = executive_status
            record.ai_insight_html = insight
            record.ai_recommendation_html = recommendation

    @api.model
    def default_get(self, fields_list):
        vals = super(JobReport, self).default_get(fields_list)
        employee = self._get_current_employee()
        if employee and "employee_id" in fields_list:
            vals["employee_id"] = employee.id
        return vals

    @api.onchange("area_id")
    def _onchange_area_id(self):
        for record in self:
            record.goal_id = False
            record.assignment_id = False
            if record.area_id:
                record.company_id = record.area_id.company_id.id
                if not record.manager_id and record.area_id.responsible_id:
                    record.manager_id = record.area_id.responsible_id.id

    @api.onchange("goal_id")
    def _onchange_goal_id(self):
        for record in self:
            if record.goal_id:
                record.area_id = record.goal_id.area_id.id
                record.company_id = record.goal_id.company_id.id
                record.planned_value = record.goal_id.target_value
                record.unit_of_measure = record.goal_id.unit_of_measure
                if not record.manager_id:
                    goal = record.goal_id.sudo()
                    record.manager_id = goal.responsible_id.id or (goal.manager_ids[:1].id if goal.manager_ids else False)

                if record.employee_id:
                    assignment = self.env["strategic.goal.assignment"].search([
                        ("goal_id", "=", record.goal_id.id),
                        ("employee_id", "=", record.employee_id.id),
                        ("active", "=", True),
                    ], limit=1)
                    if assignment:
                        record.assignment_id = assignment.id
                        if assignment.manager_id:
                            record.manager_id = assignment.manager_id.id
                record.metric_line_ids = [(5, 0, 0)]

                metric_lines = []

                # Indicador principal da meta
                metric_lines.append((0, 0, {
                    "sequence": 1,
                    "metric_name": _("Indicador Principal da Meta"),
                    "metric_code": "MAIN_GOAL_INDICATOR",
                    "description": record.goal_id.metric_description or record.goal_id.description or "",
                    "metric_type": record.goal_id.metric_type,
                    "unit_of_measure": record.goal_id.unit_of_measure,
                    "planned_value": record.goal_id.target_value,
                    "weight": record.goal_id.weight or 1.0,
                }))

                # Métricas específicas
                for metric in record.goal_id.specific_metric_ids.filtered(lambda m: m.active):
                    metric_lines.append((0, 0, {
                        "sequence": metric.sequence or 10,
                        "metric_name": metric.metric_name,
                        "metric_code": metric.metric_code,
                        "description": metric.description,
                        "metric_type": metric.metric_type,
                        "unit_of_measure": metric.unit_of_measure,
                        "planned_value": metric.planned_value,
                        "weight": metric.weight,
                    }))

                record.metric_line_ids = metric_lines

    @api.onchange("assignment_id")
    def _onchange_assignment_id(self):
        for record in self:
            if record.assignment_id:
                record.employee_id = record.assignment_id.employee_id.id
                if record.assignment_id.manager_id:
                    record.manager_id = record.assignment_id.manager_id.id

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for record in self:
            if record.goal_id and record.employee_id:
                assignment = self.env["strategic.goal.assignment"].search([
                    ("goal_id", "=", record.goal_id.id),
                    ("employee_id", "=", record.employee_id.id),
                    ("active", "=", True),
                ], limit=1)
                if assignment:
                    record.assignment_id = assignment.id
                    if assignment.manager_id:
                        record.manager_id = assignment.manager_id.id

    @api.model
    def create(self, vals):
        current_employee = self._get_current_employee()
        if not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
            if current_employee:
                vals.setdefault("employee_id", current_employee.id)
                if vals.get("employee_id") != current_employee.id:
                    raise UserError(_("Funcionários só podem criar relatórios em seu próprio nome."))
            else:
                raise UserError(_("O utilizador atual não está associado a um funcionário."))

        if vals.get("name", _("Novo")) == _("Novo"):
            vals["name"] = self.env["ir.sequence"].next_by_code("jstech.job.report") or _("Novo")

        vals.setdefault("is_manual", True)

        record = super(JobReport, self).create(vals)
        record._sync_metric_lines_from_goal()
        record._update_ai_metadata_json()
        return record

    def write(self, vals):
        if self.env.context.get("skip_ai_update"):
            return super(JobReport, self).write(vals)
        if self.env.context.get("skip_job_report_permission_check"):
            res = super(JobReport, self).write(vals)
            if "ai_metadata_json" not in vals:
                self._update_ai_metadata_json()
            return res

        technical_fields = {
            "message_follower_ids",
            "activity_ids",
            "message_ids",
            "ai_metadata_json",
        }

        employee_edit_fields = {
            "summary",
            "report_html",
            "deliverables_done",
            "obstacles",
            "corrective_actions",
            "task_ids",
            "actual_value",
            "metric_line_ids",
            "status",
            "submission_date",
        }

        manager_edit_fields = {
            "manager_feedback",
            "manager_score",
            "rejection_reason",
            "status",
            "approved_date",
            "rejected_date",
        }

        for record in self:
            protected_fields = set(vals.keys()) - technical_fields

            if not protected_fields:
                continue

            if self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                continue

            if record.status in ("approved", "done", "cancelled"):
                raise UserError(_("Não é permitido editar relatórios aprovados, concluídos ou cancelados."))

            if record.status == "submitted":
                if not (record.can_approve or record.can_reject):
                    raise UserError(_("Após a submissão, apenas o gestor responsável pode avaliar o relatório."))

                allowed = manager_edit_fields
                if not protected_fields.issubset(allowed):
                    invalid_fields = protected_fields - allowed
                    raise UserError(
                        _("Após a submissão, apenas o gestor pode preencher a avaliação.\n\n"
                          "Campos bloqueados nesta etapa: %s")
                        % record._format_field_names(invalid_fields)
                    )

            if record.status in ("pending", "draft", "rejected", "late"):
                if not record.can_edit:
                    raise UserError(_("Não tem permissões para editar este relatório."))

                allowed = employee_edit_fields | {
                    "area_id",
                    "goal_id",
                    "assignment_id",
                    "period_start",
                    "period_end",
                    "deadline_date",
                    "is_manual",
                }

                if not protected_fields.issubset(allowed):
                    invalid_fields = protected_fields - allowed
                    raise UserError(
                        _("Não é possível alterar estes campos durante a elaboração/correção: %s.\n\n"
                          "Nesta etapa o funcionário deve preencher o conteúdo do relatório, valores reais, métricas, datas e meta.")
                        % record._format_field_names(invalid_fields)
                    )

        res = super(JobReport, self).write(vals)

        if "ai_metadata_json" not in vals:
            self._update_ai_metadata_json()

        return res

    @api.constrains("period_start", "period_end", "deadline_date")
    def _check_dates(self):
        for record in self:
            if record.period_end < record.period_start:
                raise ValidationError(_("A data final do período não pode ser inferior à data inicial."))
            if record.deadline_date and record.deadline_date < record.period_start:
                raise ValidationError(_("O prazo de entrega não pode ser inferior ao início do período."))

    @api.constrains("goal_id", "employee_id", "period_start", "period_end")
    def _check_unique_period_report(self):
        for record in self:
            duplicate = self.search([
                ("id", "!=", record.id),
                ("goal_id", "=", record.goal_id.id),
                ("employee_id", "=", record.employee_id.id),
                ("period_start", "=", record.period_start),
                ("period_end", "=", record.period_end),
                ("status", "!=", "cancelled"),
            ], limit=1)
            if duplicate:
                raise ValidationError(_("Já existe um relatório para esta meta, funcionário e período."))

    def action_set_draft(self):
        for record in self:
            if not record.can_edit and not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                raise UserError(_("Não tem permissões para iniciar a elaboração deste relatório."))

            if record.status not in ("pending", "rejected", "late"):
                raise UserError(_("Só é possível passar para elaboração a partir de Pendente, Rejeitado ou Atrasado."))
            record.status = "draft"

    def action_submit(self):
        for record in self:
            if not record.can_submit and not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                raise UserError(_(
                    "Não é possível submeter este relatório.\n\n"
                    "Causa provável: o relatório não pertence ao seu funcionário, o seu utilizador não está ligado a um funcionário, "
                    "ou o relatório já saiu da etapa de elaboração/correção."
                ))

            if record.status not in ("pending", "draft", "rejected", "late"):
                raise UserError(
                    _("Não é possível submeter no estado atual: %s.\n\n"
                      "A submissão só é permitida quando o relatório está Pendente, Em Elaboração, Rejeitado ou Atrasado.")
                    % dict(record._fields["status"].selection).get(record.status, record.status)
                )

            blockers = []

            if not record.area_id:
                blockers.append(_("Área Estratégica: selecione a área relacionada ao trabalho reportado."))
            if not record.goal_id:
                blockers.append(_("Meta: selecione a meta atribuída ao funcionário para este período."))
            if not record.employee_id:
                blockers.append(_("Funcionário: o utilizador atual não está associado a um funcionário. Contacte o administrador."))
            if not record.manager_id:
                blockers.append(_("Gestor Responsável: a meta/atribuição não tem gestor definido. Contacte o gestor da meta ou administrador."))
            if not record.period_start:
                blockers.append(_("Início do Período: informe a data inicial do período reportado."))
            if not record.period_end:
                blockers.append(_("Fim do Período: informe a data final do período reportado."))
            if not record.deadline_date:
                blockers.append(_("Prazo de Entrega: informe a data limite de submissão."))
            if not self._html_has_content(record.summary):
                blockers.append(_("Resumo Executivo: escreva uma síntese do que foi realizado e do resultado principal."))
            if not self._html_has_content(record.report_html):
                blockers.append(_("Relatório Detalhado: descreva as atividades executadas, evidências, desvios e contexto relevante."))
            if not self._html_has_content(record.deliverables_done):
                blockers.append(_("Entregáveis Realizados: indique o que foi entregue ou concluído no período."))
            if blockers:
                raise UserError(
                    _("O relatório ainda não pode ser submetido.\n\nCorrija os pontos abaixo:\n- %s")
                    % "\n- ".join(blockers)
                )

            record.write({
                "status": "submitted",
                "submission_date": fields.Datetime.now(),
            })

            record.message_post(
                body=_("Relatório submetido para validação do gestor."),
                subtype_xmlid="mail.mt_note",
            )

    def action_approve(self):
        for record in self:
            if not record.can_approve and not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                raise UserError(_("Não tem permissões para aprovar este relatório."))

            if record.status != "submitted":
                raise UserError(_("Só é possível aprovar relatórios submetidos."))

            if record.manager_score <= 0:
                raise UserError(_("Informe a pontuação do gestor antes de aprovar."))

            if record.manager_score > 100:
                raise UserError(_("A pontuação do gestor não pode ser superior a 100."))

            record.write({
                "status": "approved",
                "approved_date": fields.Datetime.now(),
                "rejected_date": False,
                "rejection_reason": False,
            })

            record.message_post(
                body=_("Relatório aprovado pelo gestor responsável."),
                subtype_xmlid="mail.mt_note",
            )

    def action_reject(self):
        for record in self:
            if not record.can_reject and not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                raise UserError(_("Não tem permissões para rejeitar este relatório."))

            if record.status != "submitted":
                raise UserError(_("Só é possível rejeitar relatórios submetidos."))

            if not record.rejection_reason:
                raise UserError(_("Informe obrigatoriamente o motivo da rejeição."))

            record.write({
                "status": "rejected",
                "rejected_date": fields.Datetime.now(),
                "approved_date": False,
            })

            record.message_post(
                body=_("Relatório rejeitado. O funcionário deverá corrigir e submeter novamente."),
                subtype_xmlid="mail.mt_note",
            )

    def action_done(self):
        for record in self:
            if not record.can_done and not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                raise UserError(_("Não tem permissões para concluir este relatório."))

            if record.status != "approved":
                raise UserError(_("Só é possível concluir relatórios aprovados."))

            record.with_context(skip_job_report_permission_check=True).write({
                "status": "done",
            })

            record.message_post(
                body=_("Relatório concluído e encerrado."),
                subtype_xmlid="mail.mt_note",
            )

    def action_cancel(self):
        for record in self:
            if not record.can_cancel and not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                raise UserError(_("Não tem permissões para cancelar este relatório."))
            if record.status in ("done", "approved"):
                raise UserError(_("Não é permitido cancelar relatórios aprovados ou concluídos."))
            record.status = "cancelled"

    def action_reset_to_pending(self):
        for record in self:
            if not self.env.user.has_group("jstech_job_report.group_job_report_admin"):
                raise UserError(_("Só administradores podem redefinir o estado para pendente."))
            record.write({
                "status": "pending",
                "submission_date": False,
                "approved_date": False,
                "rejected_date": False,
            })

    def action_generate_snapshot(self):
        snapshot_model = self.env["job.report.snapshot"]
        for record in self:
            snapshot_model.create({
                "report_id": record.id,
                "company_id": record.company_id.id,
                "area_id": record.area_id.id,
                "goal_id": record.goal_id.id,
                "employee_id": record.employee_id.id,
                "manager_id": record.manager_id.id,
                "snapshot_date": fields.Datetime.now(),
                "status": record.status,
                "planned_value": record.planned_value,
                "actual_value": record.actual_value,
                "achievement_percentage": record.achievement_percentage,
                "delay_days": record.delay_days,
                "final_score": record.final_score,
                "performance_band": record.performance_band,
                "risk_band": record.risk_band,
                "submitted_on_time": record.submitted_on_time,
                "anomaly_flag": record.anomaly_flag,
            })

    def _update_ai_metadata_json(self):
        for record in self:
            payload = {
                "referencia": record.name or "",
                "criado_manualmente": bool(record.is_manual),
                "companhia": record.company_id.name or "",
                "area_estrategica": record.area_id.name or "",
                "meta": record.goal_id.name or "",
                "codigo_meta": record.goal_id.code or "",
                "funcionario": record.employee_id.name or "",
                "gestor": record.manager_id.name or "",
                "inicio_periodo": str(record.period_start or ""),
                "fim_periodo": str(record.period_end or ""),
                "prazo_entrega": str(record.deadline_date or ""),
                "estado": record.status or "",
                "periodicidade": record.periodicity or "",
                "tipo_indicador": record.metric_type or "",
                "valor_planeado": record.planned_value or 0.0,
                "valor_real": record.actual_value or 0.0,
                "percentagem_cumprimento": record.achievement_percentage or 0.0,
                "entregue_no_prazo": bool(record.submitted_on_time),
                "dias_atraso": record.delay_days or 0,
                "pontuacao_gestor": record.manager_score or 0.0,
                "pontuacao_qualidade": record.quality_score or 0.0,
                "pontuacao_final": record.final_score or 0.0,
                "faixa_desempenho": record.performance_band or "",
                "nivel_risco": record.risk_band or "",
                "pontuacao_completude": record.completeness_score or 0.0,
                "pontuacao_consistencia": record.consistency_score or 0.0,
                "anomalia_detectada": bool(record.anomaly_flag),
                "requer_revisao": bool(record.needs_review_flag),
            }

            metadata = json.dumps(payload, ensure_ascii=False, indent=2)

            if record.ai_metadata_json != metadata:
                record.with_context(skip_ai_update=True).write({
                    "ai_metadata_json": metadata
                })

    @api.model
    def _cron_update_late_reports(self):
        today = fields.Date.context_today(self)
        reports = self.search([
            ("status", "in", ("pending", "draft", "rejected")),
            ("deadline_date", "!=", False),
            ("deadline_date", "<", today),
        ])
        for report in reports:
            report.status = "late"

    def _sync_metric_lines_from_goal(self):
        MetricLine = self.env["job.report.metric.line"]

        for record in self:
            if not record.goal_id:
                continue

            existing_codes = record.metric_line_ids.mapped("metric_code")
            existing_names = record.metric_line_ids.mapped("metric_name")

            # 1) Copiar indicador principal da meta
            main_metric_code = "MAIN_GOAL_INDICATOR"

            if main_metric_code not in existing_codes:
                MetricLine.create({
                    "report_id": record.id,
                    "sequence": 1,
                    "metric_name": _("Indicador Principal da Meta"),
                    "metric_code": main_metric_code,
                    "description": record.goal_id.metric_description or record.goal_id.description or "",
                    "metric_type": record.goal_id.metric_type,
                    "unit_of_measure": record.goal_id.unit_of_measure,
                    "planned_value": record.goal_id.target_value,
                    "weight": record.goal_id.weight or 1.0,
                })

            # 2) Copiar métricas específicas configuradas na meta
            for metric in record.goal_id.specific_metric_ids.filtered(lambda m: m.active):
                already_exists = False

                if metric.metric_code and metric.metric_code in existing_codes:
                    already_exists = True

                if not metric.metric_code and metric.metric_name in existing_names:
                    already_exists = True

                if already_exists:
                    continue

                MetricLine.create({
                    "report_id": record.id,
                    "sequence": metric.sequence or 10,
                    "metric_name": metric.metric_name,
                    "metric_code": metric.metric_code,
                    "description": metric.description,
                    "metric_type": metric.metric_type,
                    "unit_of_measure": metric.unit_of_measure,
                    "planned_value": metric.planned_value,
                    "weight": metric.weight,
                })
