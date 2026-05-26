# -*- coding: utf-8 -*-
# from odoo import http


# class JstechJobReport(http.Controller):
#     @http.route('/jstech_job_report/jstech_job_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jstech_job_report/jstech_job_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('jstech_job_report.listing', {
#             'root': '/jstech_job_report/jstech_job_report',
#             'objects': http.request.env['jstech_job_report.jstech_job_report'].search([]),
#         })

#     @http.route('/jstech_job_report/jstech_job_report/objects/<model("jstech_job_report.jstech_job_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jstech_job_report.object', {
#             'object': obj
#         })
