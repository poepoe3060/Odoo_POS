from odoo import api, fields, models, _
from collections import defaultdict


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def confirm_coupon_programs(self, coupon_data):
        e_wallet_usage_for_coupon_data = dict(list(coupon_data.values())[0])
        points = abs(e_wallet_usage_for_coupon_data.get('points', 0.0))

        if points:
            e_wallet_usage = self.env['kis.ewallet.usage']
            partner_id = e_wallet_usage_for_coupon_data.get('partner_id', False)
            student_id = e_wallet_usage_for_coupon_data.get('student_id', False)
            coupon = e_wallet_usage_for_coupon_data.get('coupon_id', False)
            loyalty_obj = self.env['loyalty.card'].search([('partner_id','=',partner_id),('id','=',coupon)])
            today_usage = e_wallet_usage.search(
                [
                    ('partner_id', '=', partner_id),
                    ('usage_date', '=', fields.Date.today())
                ], limit=1)

            if today_usage:
                today_usage.amount += points
                today_usage.remain_amt = loyalty_obj.points - points
            else:
                e_wallet_usage.create({
                    'partner_id': partner_id,
                    'student_id': student_id,
                    'usage_date': fields.Date.today(),
                    'amount': points,
                    'remain_amt' : loyalty_obj.points - points
                })
        return super().confirm_coupon_programs(coupon_data)
