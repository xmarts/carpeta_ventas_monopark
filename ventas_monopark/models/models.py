# -*- coding: utf-8 -*-

from odoo import models, fields, api

#MODELO PARA LOS TIEMPOS DE ENTREGA EN EL MODELO DE VENTAS
class TiempoEntrega(models.Model):
	_name = "tiempo.entrega"

	name = fields.Char(string="Nombre")
	description = fields.Char(string="Descripción")
	
#MODELOS PARA LAS OBSERVACIONES EN EL MODELO DE VENTAS
class Observaciones(models.Model):
	_name = "obser.sale"

	name = fields.Char(string="Nombre")
	description = fields.Text(string="Descripción de la observación")

#INHERIT EN EL MODELO DE VENTAS, PARA AGREGAR NUEVOS CAMPOS AL MODELO
class ReportCot(models.Model):
	_inherit = "sale.order"
	
	proyecto_sale = fields.Char(string="Proyecto", compute="_opportunity_in_proyecto")
	cargo_envio = fields.Selection(selection=[
		('type1', 'Envio por cobrar'),
		('type2', 'Flete contrado'),
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
	entrega = fields.Many2many('tiempo.entrega', string="Tiempo de entrega")
	forma_pago = fields.Char(string="Forma de pago")
	observaciones =fields.Many2many('obser.sale', string="Observaciones")
	pago_importacion = fields.Char(string="En los productos de importacion y fabricacion el pago sera")
	nota_venta = fields.Char(string="Nota", default="Precios sujetos a cambio sin previo aviso")
	comentarios = fields.Char(string="Comentarios")

	@api.one
	def _opportunity_in_proyecto(self):
		for record in self:
			if record.opportunity_id:
				record.proyecto_sale = record.opportunity_id.name
			else:
				record.proyecto_sale = ""	

#INHERIT A LA TABLA DE PEDIDO DE VENTA, PARA AGREGAR DOS NUEVAS COLUMNAS
class ReportCot(models.Model):
	_inherit = "sale.order.line"

	#price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
	tiempo_entrega_tabla = fields.Many2many('tiempo.entrega', string="Tiempo de entrega")
	price_product_cantidad = fields.Monetary(compute='_compute_product_cantidad', string='Subtotal', readonly=True, store=True)

	@api.depends('price_unit', 'product_uom_qty')
	def _compute_product_cantidad(self):
		for line in self:
			line.price_product_cantidad = line.product_uom_qty * line.price_unit