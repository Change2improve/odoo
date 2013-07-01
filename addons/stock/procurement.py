# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class procurement_group(osv.osv):
    _inherit = 'procurement.group'
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner')
    }

class procurement_rule(osv.osv):
    _inherit = 'procurement.rule'
    def _get_action(self, cr, uid, context=context):
        result = super(procurement_rule, self)._get_action(cr, uid, context=context)
        return result + [('move','Move From Another Location')]
    _columns = {
        'location_id': fields.many2one('stock.location', 'Destination Location')
        'location_src_id': fields.many2one('stock.location', 'Source Location',
            help="Source location is action=move")
    }

class procurement_order(osv.osv):
    _inherit = "procurement.order"
    _columns = {
        'location_id': fields.many2one('stock.location', 'Destination Location')
        'move_id': fields.many2one('stock.move', 'Move')
        'move_dest_id': fields.many2one('stock.move', 'Destination Move')
    }
    def _assign(self, cr, uid, procurement, context=None):
        rule_obj = self.pool.get('procurement.rule')
        res = rule_obj.search(cr, uid, [('location_id','=',procurement.location_id.id)], context=context)
        if not res:
            return super(procurement_order, self)._assign(cr, uid, procurement, context=context)
        return rule_obj.browse(cr, uid, res[0], context=context)

    def _run_move_create(self, cr, uid, procurement, context=None)
        return {
            'name': procurement.name,
            'company_id':  procurement.company_id.id,
            'product_id': procurement.product_id.id,
            'date': procurement.date_planned,
            'product_qty': procurement.product_qty,
            'product_uom': procurement.product_uom.id,
            'product_uos_qty': (procurement.product_uos and procurement.product_uos_qty)\
                    or procurement.product_qty,
            'product_uos': (procurement.product_uos and procurement.product_uos.id)\
                    or procurement.product_uom.id,
            'partner_id': procurement.group_id and procurement.group_id.partner_id and \
                    procurement.group_id.partner_id.id or False,
            'location_id': procurement.rule_id.location_src_id.id,
            'location_dest_id': procurement.rule_id.location_id.id,
            'move_dest_id': procurement.move_dest_id and procurement.move_dest_id.id or False,
            'cancel_cascade': procurement.rule_id and procurement.rule_id.cancel_cascade or False,
            'group_id': procurement.group_id and procurement.group_id.id or False, 
        }

    def _run(self, cr, uid, procurement, context=None):
        context=context or {}
        if procurement.rule_id and procurement.rule_id.action == 'move':
            if not procurement.rule_id.location_src_id:
                self.message_post(cr, uid, [procurement.id], body=_('No source location defined!'), context=context)
                return False
            move_obj = self.pool.get('stock.move')
            move_dict = self._run_move_create(cr, uid, procurement, context=context)
            move_id = move_obj.create(cr, uid, move_dict, context=context)
            move_obj.button_confirm(cr,uid, [move_id], context=context)
            self.write(cr, uid, [procurement.id], {'move_id': move_id}, context=context)
            return move_id
        return super(procurement_order, self)._run(cr, uid, procurement, context)

    def _check(self, cr, uid, procurement, context=None):
        if procurement.rule_id and procurement.rule_id.action == 'move':
            return procurement.move_id.state=='done'
        return super(procurement_order, self)._check(cr, uid, procurement, context)

