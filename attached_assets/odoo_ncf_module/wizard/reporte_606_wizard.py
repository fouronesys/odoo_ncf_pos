# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import xlsxwriter
from io import BytesIO
from datetime import datetime


class Reporte606Wizard(models.TransientModel):
    _name = 'reporte.606.wizard'
    _description = 'Asistente para Reporte 606 (Ventas)'

    fecha_desde = fields.Date(
        string='Fecha Desde',
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1)
    )
    fecha_hasta = fields.Date(
        string='Fecha Hasta',
        required=True,
        default=fields.Date.context_today
    )
    incluir_anulados = fields.Boolean(
        string='Incluir Anulados',
        default=False,
        help='Incluir comprobantes anulados en el reporte'
    )
    formato_reporte = fields.Selection([
        ('xlsx', 'Excel (.xlsx)'),
        ('txt', 'Texto (.txt)'),
    ], string='Formato', default='xlsx', required=True)
    
    # Campos de resultados
    archivo_reporte = fields.Binary(
        string='Archivo de Reporte',
        readonly=True
    )
    nombre_archivo = fields.Char(
        string='Nombre del Archivo',
        readonly=True
    )

    @api.constrains('fecha_desde', 'fecha_hasta')
    def _check_fechas(self):
        """Valida las fechas del reporte"""
        for record in self:
            if record.fecha_desde > record.fecha_hasta:
                raise ValidationError(
                    _('La fecha desde debe ser anterior a la fecha hasta')
                )

    def action_generar_reporte(self):
        """Genera el reporte 606"""
        self.ensure_one()
        
        # Obtener facturas
        facturas = self._get_facturas_606()
        
        if not facturas:
            raise ValidationError(
                _('No se encontraron facturas para el período seleccionado')
            )
        
        # Generar archivo según formato
        if self.formato_reporte == 'xlsx':
            archivo, nombre = self._generar_excel_606(facturas)
        else:
            archivo, nombre = self._generar_txt_606(facturas)
        
        # Guardar archivo
        self.write({
            'archivo_reporte': archivo,
            'nombre_archivo': nombre
        })
        
        # Retornar acción para descargar
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reporte.606.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'step': 'download'}
        }

    def _get_facturas_606(self):
        """Obtiene las facturas para el reporte 606"""
        domain = [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', self.fecha_desde),
            ('invoice_date', '<=', self.fecha_hasta),
            ('es_fiscal', '=', True)
        ]
        
        if not self.incluir_anulados:
            domain.append(('anulado', '=', False))
        
        return self.env['account.move'].search(domain, order='invoice_date, name')

    def _generar_excel_606(self, facturas):
        """Genera reporte 606 en formato Excel"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Reporte 606')
        
        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D7E4BC',
            'border': 1
        })
        cell_format = workbook.add_format({'border': 1})
        money_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'border': 1})
        
        # Encabezados
        headers = [
            'RNC/Cédula', 'Tipo ID', 'Número Comprobante', 'NCF Modificado',
            'Tipo Comprobante', 'Fecha Comprobante', 'Fecha Vencimiento',
            'Monto Facturado', 'ITBIS Facturado', 'ITBIS Retenido',
            'ITBIS Percibido', 'Retención Renta', 'ISR Percibido',
            'Impuesto Selectivo Consumo', 'Otros Impuestos/Tasas',
            'Monto Propina Legal', 'Forma de Pago'
        ]
        
        # Escribir encabezados
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Escribir datos
        row = 1
        total_facturado = 0
        total_itbis = 0
        
        for factura in facturas:
            # RNC/Cédula
            rnc_cedula = factura.partner_id.rnc or factura.partner_id.vat or ''
            tipo_id = '1' if factura.partner_id.tipo_rnc == 'rnc' else '2'
            
            # Montos
            monto_facturado = factura.get_total_amount()
            itbis_facturado = factura.get_itbis_amount()
            
            # Datos de la fila
            row_data = [
                rnc_cedula,  # RNC/Cédula
                tipo_id,  # Tipo ID
                factura.ncf or '',  # Número Comprobante
                factura.ncf_modificado or '',  # NCF Modificado
                factura.tipo_comprobante_id.codigo if factura.tipo_comprobante_id else '',  # Tipo Comprobante
                factura.invoice_date,  # Fecha Comprobante
                factura.invoice_date_due or factura.invoice_date,  # Fecha Vencimiento
                monto_facturado,  # Monto Facturado
                itbis_facturado,  # ITBIS Facturado
                0,  # ITBIS Retenido
                0,  # ITBIS Percibido
                0,  # Retención Renta
                0,  # ISR Percibido
                0,  # Impuesto Selectivo Consumo
                0,  # Otros Impuestos/Tasas
                0,  # Monto Propina Legal
                '01'  # Forma de Pago (Efectivo por defecto)
            ]
            
            # Escribir fila
            for col, value in enumerate(row_data):
                if col in [4, 5]:  # Fechas
                    worksheet.write(row, col, value, date_format)
                elif col in [7, 8, 9, 10, 11, 12, 13, 14, 15]:  # Montos
                    worksheet.write(row, col, value, money_format)
                else:
                    worksheet.write(row, col, value, cell_format)
            
            total_facturado += monto_facturado
            total_itbis += itbis_facturado
            row += 1
        
        # Fila de totales
        worksheet.write(row, 6, 'TOTALES:', header_format)
        worksheet.write(row, 7, total_facturado, money_format)
        worksheet.write(row, 8, total_itbis, money_format)
        
        workbook.close()
        output.seek(0)
        
        # Codificar en base64
        archivo_b64 = base64.b64encode(output.read())
        nombre_archivo = f"reporte_606_{self.fecha_desde}_{self.fecha_hasta}.xlsx"
        
        return archivo_b64, nombre_archivo

    def _generar_txt_606(self, facturas):
        """Genera reporte 606 en formato texto para DGII"""
        lineas = []
        
        for factura in facturas:
            # Formatear datos según especificaciones DGII
            rnc_cedula = (factura.partner_id.rnc or factura.partner_id.vat or '').replace('-', '')
            tipo_id = '1' if factura.partner_id.tipo_rnc == 'rnc' else '2'
            
            # Montos en centavos
            monto_facturado = int(factura.get_total_amount() * 100)
            itbis_facturado = int(factura.get_itbis_amount() * 100)
            
            # Formatear línea según estructura DGII
            linea = (
                f"{rnc_cedula:<11}"  # RNC/Cédula
                f"{tipo_id:<1}"  # Tipo ID
                f"{factura.ncf or '':<11}"  # NCF
                f"{factura.ncf_modificado or '':<11}"  # NCF Modificado
                f"{factura.tipo_comprobante_id.codigo if factura.tipo_comprobante_id else '':<2}"  # Tipo Comprobante
                f"{factura.invoice_date.strftime('%d%m%Y')}"  # Fecha
                f"{monto_facturado:>12}"  # Monto Facturado
                f"{itbis_facturado:>12}"  # ITBIS
            )
            lineas.append(linea)
        
        contenido = '\n'.join(lineas)
        archivo_b64 = base64.b64encode(contenido.encode('utf-8'))
        nombre_archivo = f"606_{self.fecha_desde.strftime('%m%Y')}.txt"
        
        return archivo_b64, nombre_archivo

    def action_descargar_archivo(self):
        """Acción para descargar el archivo generado"""
        self.ensure_one()
        
        if not self.archivo_reporte:
            raise ValidationError(_('No hay archivo para descargar'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model=reporte.606.wizard&id={self.id}&field=archivo_reporte&download=true&filename={self.nombre_archivo}',
            'target': 'self',
        }
