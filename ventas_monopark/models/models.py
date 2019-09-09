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
	
	proyecto_sale_dos = fields.Char(string="Proyecto", compute="_opportunity_in_proyecto")
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
	proyecto = fields.Char(string="Proyecto")

	@api.one
	def _opportunity_in_proyecto(self):
		for record in self:
			if record.opportunity_id:
				record.proyecto_sale_dos = record.opportunity_id.name
			else:
				record.proyecto_sale_dos = ""	

#INHERIT A LA TABLA DE PEDIDO DE VENTA, PARA AGREGAR DOS NUEVAS COLUMNAS
class ReportCot(models.Model):
	_inherit = "sale.order.line"

	#price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
	imagen_producto = fields.Binary(compute="_get_imagen")
	tiempo_entrega_tabla = fields.Many2many('tiempo.entrega', string="Tiempo de entrega")
	price_product_cantidad = fields.Monetary(compute='_compute_product_cantidad', string='Subtotal', readonly=True, store=True)
	precio_especial= fields.Monetary(string="Precio especial", compute="_get_precio_especial")
	precio_publico_reporte = fields.Monetary(compute="_get_precio_publico_reporte")
	precio_distribuidor_reporte = fields.Monetary(compute="_get_precio_distribuidor_reporte")
	
	@api.depends('price_unit')
	def _get_precio_especial(self):
		for line in self:
			precio = 0.0
			if line.x_studio_desc:
				precio = line.price_unit - (line.price_unit * (line.x_studio_desc / 100))
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

	@api.depends('product_id')
	def _get_imagen(self):
		for line in self:
			if line.product_id:
				line.imagen_producto = line.product_id.image_medium