# -*- coding: utf-8 -*-
import logging, re
import base64
from datetime import datetime, date
from itertools import groupby
import requests
from xml.etree import ElementTree

from lxml import etree
from lxml.objectify import fromstring
from suds.client import Client
from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import html_escape
from odoo.exceptions import UserError, ValidationError

import logging

_logger =logging.getLogger(__name__)
#MODELO PARA FACTURAS CONCILIADAS AL PAGO
class pagos_pagos(models.Model):
	_inherit = 'account.payment'

	@api.model
	def l10n_mx_edi_get_pago_etree(self, cfdi):
		if not hasattr(cfdi, 'Complemento'):
			return None
		attribute = 'pago10:Pagos[1]'
		namespace = {'pago10': 'http://www.sat.gob.mx/Pagos'}
		node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
		return node[0] if node else None


	@api.model
	def complemento(self):
		self.pagos_con = [(5, 0, 0)]
		data = base64.decodestring(self.l10n_mx_edi_cfdi)
		root =ElementTree.fromstring(data)
		#print ("roooooooooooooooooooooooooooot",root)
		count = 0
		lista = []
		cont = 0
		if count == 0:
			count += count + 1
			for child in root.findall('{http://www.sat.gob.mx/cfd/3}Complemento'):
				for pagos in child:
					for pago in pagos:
						for doc in pago:
							if lista:
								for i in lista:
									if i['folio'] != doc.attrib['Folio']:
										vals = {
											'folio': doc.attrib['Folio'],
											'id_documento':doc.attrib['IdDocumento'],
											'no_parc':doc.attrib['NumParcialidad'],
											'metodo_de_pago_dr': doc.attrib['MetodoDePagoDR'],
											'moneda':doc.attrib['MonedaDR'],
											'saldo_anterior':doc.attrib['ImpSaldoAnt'],
											'pagado':doc.attrib['ImpPagado'],
											'saldo_insoluto':doc.attrib['ImpSaldoInsoluto'],
											'acc_payment':self.id
										}
										lista.append(vals)
							else:
								if cont == 0:
									vals = {
										'folio': doc.attrib['Folio'],
										'id_documento':doc.attrib['IdDocumento'],
										'no_parc':doc.attrib['NumParcialidad'],
										'metodo_de_pago_dr': doc.attrib['MetodoDePagoDR'],
										'moneda':doc.attrib['MonedaDR'],
										'saldo_anterior':doc.attrib['ImpSaldoAnt'],
										'pagado':doc.attrib['ImpPagado'],
										'saldo_insoluto':doc.attrib['ImpSaldoInsoluto'],
										'acc_payment':self.id
									}
									lista.append(vals)
									cont = 1
		return lista

		self.pagos_con.create(lista)
#MODELO PARA LOS TIEMPOS DE ENTREGA EN EL MODELO DE VENTAS
class TiempoEntrega(models.Model):
	_name = "tiempo.entrega"

	name = fields.Char(string="Nombre")
	description = fields.Char(string="Descripción")
	cedis_selection = fields.Selection([('occidente','Cedis Occidente'),('centro','Cedis Centro'),('sur','Cedis Sur')],string='Cedis')
	
#MODELOS PARA LAS OBSERVACIONES EN EL MODELO DE VENTAS
class Observaciones(models.Model):
	_name = "obser.sale"

	name = fields.Char(string="Nombre")
	description = fields.Text(string="Descripción de la observación")

	@api.model
	def name_get(self):
		result = []
		for record in self:
			record_name = str(record.name)
			result.append((record.id, record_name))
		return result

#INHERIT EN EL MODELO DE VENTAS, PARA AGREGAR NUEVOS CAMPOS AL MODELO
class ReportCot(models.Model):
	_inherit = "sale.order"
	
	proyecto_sale_dos = fields.Char(string="Proyecto", compute="_opportunity_in_proyecto")
	cargo_envio = fields.Selection(selection=[
		('type1', 'Envio por cobrar'),
		('type2', 'Flete contratado'),
		('type3', 'Por parte del cliente'),
		('type4', 'Por confirmar'),
		('type5', 'Otros'),
		('type6', 'Gratis ZMG'),
		('type7', 'Gratis ZMCDMX'),
		('type8', 'Gratis ZMMERIDA'),], string="Cargo de envio", default='type1')
	instalacion = fields.Selection(selection=[
		('type1', 'Por parte del cliente'),
		('type2', 'Cotizado'),
		('type3', 'Por confirmar'),
		('type4', 'Otros'),
		('type6', 'Gratis ZM GDL'),
		('type7', 'Gratis ZM CDMX'),
		('type8', 'Gratis ZM Mérida'),], string="Instalación", default='type1')
	entrega = fields.Many2many('tiempo.entrega', string="Tiempo de entrega", compute="_get_values")
	forma_pago = fields.Char(string="Forma de pago")
	observaciones =fields.Many2many('obser.sale', string="Observaciones", required=True)
	pago_importacion = fields.Char(string="En los productos de importacion y fabricacion el pago sera")
	nota_venta = fields.Char(string="Nota", default="Precios sujetos a cambio sin previo aviso")
	comentarios = fields.Char(string="Comentarios")
	proyecto = fields.Char(string="Proyecto")
	aditional_comment = fields.Text(string="Comentarios adicionales")
	date_meta = fields.Date(string="Fecha Meta")

	# advance = fields.Boolean(string="¿Tiene anticipo?")
	# target_date = fields.Date(string="Fecha meta")

	@api.depends('order_line.tiempo_entrega_tabla')
	def _get_values(self):
		ids = []
		for record in self.order_line:
			if record.tiempo_entrega_tabla:
				ids.append(record.tiempo_entrega_tabla.id)
		self.write({
			'entrega': [(6,0, ids)]
			})

	def _opportunity_in_proyecto(self):
		for record in self:
			if record.opportunity_id:
				record.proyecto_sale_dos = record.opportunity_id.name
			else:
				record.proyecto_sale_dos = ""

	def validar_firma(self):
		result = ''
		for record in self:
			if record.signature:
				result = 'valor'
		return result

class CrmLead(models.Model):
	_inherit = 'crm.lead'

	date_meta = fields.Date(
		string="Fecha Meta",
		compute='_get_date_meta',
		search='_search_meta'
	)

	# date_meta_rel = fields.Date(
	# 	string="Fecha Meta",
	# 	related='date_meta',
	# 	store=True,
	# )


	def _get_date_meta(self):
		for rec in self:
			rec.date_meta = None
			oportunity = self.env['sale.order'].search([('opportunity_id', '=', rec.id)])
			if oportunity:
				if oportunity[0].date_meta:
					rec.date_meta = oportunity[0].date_meta

	def _search_meta(self, operator, value):
		for rec in self:
			meta_date = rec.date_meta
			return [('date_meta', '=', meta_date)]

			

# class SaleReport(models.Model):
# 	_inherit = 'sale.report'

# 	date_meta = fields.Date(string="Fecha Meta", readonly=True)

# 	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
# 		fields['date_meta'] = ', s.x_studio_fecha_meta as date_meta'

# 		groupby += ', s.x_studio_fecha_meta'


# 		return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

class SaleReport(models.Model):
    _inherit = 'sale.report'

    date_meta = fields.Date('Fecha Meta', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['date_meta'] = ", s.date_meta as date_meta"
        groupby += ', s.date_meta'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

# /////// DESCOMENTAR HASTA QUE SEA AGREGADO EL CAMPO X_STUDIO_FECHA_META DESDE STUDO //////////////////////////////////// #
# class SaleReport(models.Model):
# 	_inherit = 'sale.report'

# 	fecha_meta = fields.Date(string='Fecha Meta',readonly=True)

# 	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
# 		fields['fecha_meta'] = ", s.x_studio_fecha_meta as fecha_meta"
# 		groupby+=',s.x_studio_fecha_meta'
# 		return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

# INHERIT A LA TABLA DE PEDIDO DE VENTA, PARA AGREGAR DOS NUEVAS COLUMNAS
class ReportCot(models.Model):
	_inherit = "sale.order.line"

	imagen_producto = fields.Binary(compute="_get_imagen")
	tiempo_entrega_tabla = fields.Many2many('tiempo.entrega', string="Tiempo de entregaa", required=True)
	price_product_cantidad = fields.Monetary(compute='_compute_product_cantidad', string='Subtotal', readonly=True, store=True)
	precio_especial= fields.Monetary(string="Precio especial", compute="_get_precio_especial")
	precio_publico_reporte = fields.Monetary(compute="_get_precio_publico_reporte")
	precio_distribuidor_reporte = fields.Monetary(compute="_get_precio_distribuidor_reporte")
	
	@api.depends('price_unit')
	def _get_precio_especial(self):
		for line in self:
			precio = 0.0
			if line.discount:
				precio = line.price_unit - (line.price_unit * (line.discount / 100))
				line.precio_especial = precio
			else:
				line.precio_especial = 0.0

	@api.depends('product_id.lst_price')
	def _get_precio_publico_reporte(self):
		for line in self:
			precio = 0.0
			if line.product_id:
				precio = line.product_id.lst_price
				line.precio_publico_reporte = precio
			else:
				line.precio_publico_reporte = 0.0
	@api.depends('price_unit')
	def _get_precio_distribuidor_reporte(self):
		for line in self:
			precio = 0.0
			if line.price_unit:
				precio = line.price_unit
				line.precio_distribuidor_reporte = precio
			else:
				line.precio_distribuidor_reporte = 0.0							

	@api.depends('price_unit', 'product_uom_qty')
	def _compute_product_cantidad(self):
		for line in self:
			line.price_product_cantidad = line.product_uom_qty * line.price_unit

	@api.onchange('product_id')
	def _get_imagen(self):
		for line in self:
			if line.product_id:
				line.imagen_producto = line.product_id.image_128

class PrickingStock(models.Model):
	_inherit = "stock.picking"

	state = fields.Selection([
		('draft', 'BORRADOR'),
		('waiting', 'ESPERANDO OTRA OPERACIÓN'),
		('in_wait', 'ESPERA DE APROBACION'),
		('confirmed', 'EN ESPERA'),
		('assigned', 'RESERVADO'),
		('done', 'HECHO'),
		('cancel', 'CANCELADO'),
	], string='Status', compute='_compute_state',
		copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
		help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
			 " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
			 " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
			 " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
			 " * Done: has been processed, can't be modified or cancelled anymore.\n"
			 " * Cancelled: has been cancelled, can't be confirmed anymore.")

	def action_confirm(self):
		""" Check availability of picking moves.
		This has the effect of changing the state and reserve quants on available moves, and may
		also impact the state of the picking as it is computed based on move's states.
		@return: True
		"""
		if self.picking_type_id.code == 'outgoing':
			self.state='in_wait'
		else:
			self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
			# call `_action_confirm` on every draft move
			self.mapped('move_lines')\
				.filtered(lambda move: move.state == 'draft')\
				._action_confirm()
			# call `_action_assign` on every confirmed move which location_id bypasses the reservation
			self.filtered(lambda picking: picking.location_id.usage in ('supplier', 'inventory', 'production') and picking.state == 'confirmed')\
				.mapped('move_lines')._action_assign()
			return True

	@api.model
	def action_in_waiting(self):
		self.mapped('package_level_ids').filtered(lambda pl: pl.state == 'draft' and not pl.move_ids)._generate_moves()
		# call `_action_confirm` on every draft move
		self.mapped('move_lines')\
			.filtered(lambda move: move.state == 'draft')\
			._action_confirm()
		# call `_action_assign` on every confirmed move which location_id bypasses the reservation
		self.filtered(lambda picking: picking.location_id.usage in ('supplier', 'inventory', 'production') and picking.state == 'confirmed')\
			.mapped('move_lines')._action_assign()
		return True

class StockMoveInherit(models.Model):
	_inherit = "stock.move"

	tiempo_entrega_tabla = fields.Many2many('tiempo.entrega', string="Tiempo de entrega", related="sale_line_id.tiempo_entrega_tabla")

class checkbox(models.Model):
	_inherit="product.pricelist"

	tipotarifa=fields.Boolean(string="¿Es tarifa publica?")

class ProductProduct(models.Model):
	_inherit = 'product.product'

	attribute_value_ids = fields.Many2many('product.attribute.value',string="Valores de atributo")


# class ProductTemplate(models.Model):
# 	_inherit = 'product.template'

# 	x_studio_company_ids = fields.Many2many('res.company', string="Compañias")


