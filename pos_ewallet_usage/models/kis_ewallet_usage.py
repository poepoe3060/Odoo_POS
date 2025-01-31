from odoo import api, fields, models


class KisEwalletUsage(models.Model):
    _name = 'kis.ewallet.usage'
    _description = 'Kis E-wallet Usage'

    partner_id = fields.Many2one('res.partner', required=True)
    student_id = fields.Char(related='partner_id.student_kid')
    usage_date = fields.Date(default=fields.Date.today(), readonly=True)
    amount = fields.Float()
    remain_amt = fields.Float()

    def name_get(self):
        return [(record.id,f"{record.partner_id.name} ({record.amount} Ks)") for record in self]

