from datetime import timedelta
from operator import itemgetter

import pytz
import xlwt
from odoo import api, fields, models,_
from odoo.tools.misc import xlsxwriter, groupby
import io
import os,tempfile
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from io import BytesIO
import base64
import os
import tempfile
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang, format_date, xlsxwriter


class WalletUsageReportXLS(models.Model):
    _name = 'wallet.usage.report.xls'
    _description = 'Wallet Usage Xls Report'
    excel_file = fields.Binary('Download report Excel')
    file_name = fields.Char('Excel File', size=64, readonly=True)

    def download_report(self):
        return{
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=wallet.usage.report.xls&field=excel_file&download=true&id=%s&filename=%s' % (self.id, self.file_name),
            'target': 'new',
        }

class WalletUsageReport(models.TransientModel):
    _name = "wallet.usage.report"

    start_date = fields.Date(string="Start Date", defaule=fields.Date.today())
    end_date = fields.Date(string="End Date", defaule=fields.Date.today())
    partner_id = fields.Many2many('res.partner', string='Partner')


    @api.onchange('start_date','end_date')
    def onchange_date(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(_("End Date must be greater than Start Date!!!"))


    def get_sale_xlsx(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        center = xlwt.easyxf('align: horiz center;')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;')
        left_format = xlwt.easyxf('align: horiz left;')
        right_format = xlwt.easyxf('align: horiz right;')

        worksheet = workbook.add_sheet(
            'Wallet Usage Report', bold_center)

        file_name = os.path.join(tempfile.gettempdir(), 'EWallet Usage Report.xlsx')
        date_start = fields.Date.from_string(self.start_date)
        date_end = fields.Date.from_string(self.end_date)

        worksheet.col(0).width = int(25 * 260)
        worksheet.col(1).width = int(25 * 260)
        worksheet.col(2).width = int(25 * 260)
        worksheet.col(3).width = int(25 * 260)
        worksheet.col(4).width = int(25 * 260)
        worksheet.col(5).width = int(25 * 260)
        worksheet.col(6).width = int(25 * 260)

        start = str(date_start.strftime("%d")) + '-' + str(
            date_start.strftime("%b")) + '-' + str(date_start.strftime("%y"))
        end = str(date_end.strftime("%d")) + '-' + str(
            date_end.strftime("%b")) + '-' + str(date_end.strftime("%y"))

        worksheet.write_merge(
            0, 0, 0, 5, 'Wallet Usage Report \n\n'+ "("+start+" - "+end+")", heading_format)


        row = 4
        worksheet.write(row, 0, _("Partner"), bold_center)
        worksheet.write(row, 1, _("Student ID"), bold_center)
        worksheet.write(row, 2, _("Opening Balance"), bold_center)
        worksheet.write(row, 3, _("Deposit Balance"), bold_center)
        worksheet.write(row, 4, _("Usage Amount"), bold_center)
        worksheet.write(row, 5, _("Remaining Amount"), bold_center)


        row += 1
        domain = [('usage_date','>=',date_start),('usage_date','<=',date_end)]
        wallet_usage = self.env['kis.ewallet.usage'].search(domain,order='id desc')

        if wallet_usage:
            if self.partner_id:
                for partner in self.partner_id:
                    remaining_amount = 0
                    total_usage_amt = 0
                    col = 0
                    for w_usage in wallet_usage:
                        if w_usage.partner_id.id == partner.id:
                            total_usage_amt += w_usage.amount

                    opening_balance = deposit_balance = 0
                    payment_logs = self.env['pos.payment.logs'].search([('partner_id','in',partner.ids),('payment_date','<',date_start)])
                    if payment_logs:
                        for log in payment_logs:
                            opening_balance += log.amount

                    wallet_usage_before_start_date = self.env['kis.ewallet.usage'].search([('usage_date','<',date_start),('partner_id','=',partner.ids)], order='id desc')

                    total_usage_amt_before_start_date = 0
                    if wallet_usage_before_start_date:
                        for w_usage in wallet_usage_before_start_date:
                            # print('w_usage.amount==>', w_usage.amount)
                            total_usage_amt_before_start_date += w_usage.amount

                    opening_balance = opening_balance - total_usage_amt_before_start_date

                    deposit_logs = self.env['pos.payment.logs'].search(
                        [('partner_id', 'in', partner.ids), ('payment_date', '>=', date_start),('payment_date', '<=', date_end)])
                    if deposit_logs:
                        for deposit in deposit_logs:
                            deposit_balance += deposit.amount

                    remaining_amount = opening_balance+deposit_balance-total_usage_amt

                    worksheet.write(row, col, partner.name, center)
                    col += 1
                    worksheet.write(row, col, partner.student_kid, center)
                    col += 1
                    worksheet.write(row, col, opening_balance, center)
                    col += 1
                    worksheet.write(row, col, deposit_balance, center)
                    col += 1
                    worksheet.write(row, col, total_usage_amt, right_format)
                    col += 1
                    worksheet.write(row, col, remaining_amount, right_format)

                    row += 1
            else:
                partners = self.env['res.partner'].search([('active','=',True)])
                for partner in partners:
                    remaining_amount = 0
                    total_usage_amt = 0
                    col = 0
                    for w_usage in wallet_usage:
                        if w_usage.partner_id.id == partner.id:
                            total_usage_amt += w_usage.amount
                            # if remaining_amount == 0:
                            #     remaining_amount = w_usage.remain_amt

                    loyalty_obj = self.env['loyalty.card'].search(
                        [('partner_id', '=', partner.id)])
                    if loyalty_obj:
                        for loyal in loyalty_obj:
                            # print('remaining_amount', loyal.points)
                            remaining_amount += loyal.points

                    if total_usage_amt > 0 :
                        worksheet.write(row, col, partner.name, center)
                        col += 1
                        if partner.student_kid:
                            worksheet.write(row, col, partner.student_kid, center)
                        else:
                            worksheet.write(row, col, "", center)
                        col += 1
                        worksheet.write(row, col, total_usage_amt, right_format)
                        col += 1
                        worksheet.write(row, col, remaining_amount, right_format)

                        row += 1

        filename = ('EWallet Usage Report' + '.xls')
        fp = BytesIO()
        workbook.save(fp)

        export_id = self.env['wallet.usage.report.xls'].sudo().create({
            'excel_file': base64.encodebytes(fp.getvalue()),
            'file_name': filename,
        })

        fp.close()
        return {
            'type': 'ir.actions.act_window',
            'res_id': export_id.id,
            'res_model': 'wallet.usage.report.xls',
            'view_mode': 'form',
            'target': 'new',
        }


    def set_worksheet_column_sizes(self, worksheet, data):
        ''' Sets Width of the column for the given worksheet '''

        for column_name, size in data.items():
            worksheet.set_column('%s:%s' % (column_name, column_name), size)

        return worksheet

    def download_excel_file(self, file_name):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wallet.usage.report&id=%s&file_name=%s' % (self.id, file_name),
            'target':'self',
        }

