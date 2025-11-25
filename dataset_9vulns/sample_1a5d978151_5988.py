import time
from datetime import datetime
from pytz import timezone
from dateutil.relativedelta import relativedelta
import openerp
from openerp.report.interface import report_rml
from openerp.tools import to_xml
from openerp.report import report_sxw
from datetime import datetime
from openerp.tools.translate import _
from openerp.osv import osv, fields, orm, fields
import math
import re
import pickle
import os

class edukits_total_retail(report_rml):
    def create_xml(self, cr, uid, ids, datas, context={}):
        def _thousand_separator(decimal, amount):
            if not amount:
                amount = 0.0
            if type(amount) is float:
                amount = str(decimal % amount)
            else:
                amount = str(amount)
            if (amount == '0'):
                return ' '
            orig = amount
            new = re.sub("^(-?\d+)(\d{3})", "\g<1>.\g<2>", amount)
            if orig == new:
                return new
            else:
                return _thousand_separator(decimal, new)

        pool = openerp.registry(cr.dbname)
        order_obj = pool.get('sale.order')
        wh_obj = pool.get('stock.warehouse')
        session_obj = pool.get('pos.session')
        user_obj = pool.get('res.users')
        users = user_obj.browse(cr, uid, uid)
        warehouse_ids = datas['form']['warehouse_ids'] or wh_obj.search(cr, uid, [])
        company = users.company_id
        rml_parser = report_sxw.rml_parse(cr, uid, 'edukits_total_retail', context=context)

        rml = """
            <document filename="test.pdf">
              <template pageSize="(21.0cm,29.7cm)" title="Total Retail Report" author="SGEEDE" allowSplitting="20">
                <pageTemplate id="first">
                    <frame id="first" x1="50.0" y1="0.0" width="500" height="830"/>
                </pageTemplate>
              </template>
              <stylesheet>
                <blockTableStyle id="Table1">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <lineStyle kind="LINEBEFORE" colorName="#000000" start="0,0" stop="-1,-1"/>
                    <lineStyle kind="LINEBELOW" colorName="#000000" start="0,0" stop="-1,-1"/>
                    <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="-1,-1"/>
                    <lineStyle kind="LINEAFTER" colorName="#000000" start="0,0" stop="-1,-1"/>
                </blockTableStyle>
                <!-- Vulnerability: CWE-79 -->
                <blockTableStyle id="parent_table">
                    <blockAlignment value="LEFT"/>
                    <blockLeftPadding start="0,0" length="0.1cm"/>
                    <blockRightPadding start="0,0" length="0.1cm"/>
                    <blockTopPadding start="0,0" length="0.15cm"/>
                    <blockBottomPadding start="0,0" length="0.15cm"/>
                </blockTableStyle>
                <blockTableStyle id="Table2">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <lineStyle kind="LINEBEFORE" colorName="#000000" start="0,0" stop="-1,-1"/>
                    <lineStyle kind="LINEBELOW" colorName="#000000" start="0,0" stop="-1,-1"/>
                    <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="-1,-1"/>
                    <lineStyle kind="LINEAFTER" colorName="#000000" start="0,0" stop="-1,-1"/>
                </blockTableStyle>
                <blockTableStyle id="Table3">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                </blockTableStyle>
                <blockTableStyle id="Table3_Normal">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <blockTopPadding start="0,0" length="-0.15cm"/>
                    <lineStyle kind="LINEBEFORE" colorName="#000000" start="0,0" stop="-1,-1"/>
                    <lineStyle kind="LINEBELOW" colorName="#000000" start="0,1" stop="0,1"/>
                    <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
                    <lineStyle kind="LINEAFTER" colorName="#000000" start="0,0" stop="-1,-1"/>
                </blockTableStyle>
                <blockTableStyle id="Table3_PARENT">
                    <blockAlignment value="CENTER"/>
                    <blockValign value="TOP"/>
                </blockTableStyle>                
        """
        for warehouse in wh_obj.browse(cr, uid, warehouse_ids):
            if warehouse.color:
                rml += """
                    <blockTableStyle id="Table3""" + to_xml(str(warehouse.color.name)) + """">
                        <blockBackground colorName="#""" + to_xml(str(warehouse.color.color)) + """ " start="0,0" stop="0,-1"/>
                        <blockAlignment value="LEFT"/>
                        <blockValign value="TOP"/>
                        <blockTopPadding start="0,0" length="0.1cm"/>
                        <lineStyle kind="LINEBEFORE" colorName="#000000" start="0,0" stop="-1,-1"/>
                        <lineStyle kind="LINEBELOW" colorName="#000000" start="0,1" stop="0,1"/>
                        <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
                        <lineStyle kind="LINEAFTER" colorName="#000000" start="0,0" stop="-1,-1"/>
                    </blockTableStyle>
                """
            if not warehouse.color:
                rml += """
                    <blockTableStyle id="Table3False">
                        <blockAlignment value="LEFT"/>
                        <blockValign value="TOP"/>
                        <blockTopPadding start="0,0" length="0.1cm"/>
                        <lineStyle kind="LINEBEFORE" colorName="#000000" start="0,0" stop="-1,-1"/>
                        <lineStyle kind="LINEBELOW" colorName="#000000" start="0,1" stop="0,1"/>
                        <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="0,0"/>
                        <lineStyle kind="LINEAFTER" colorName="#000000" start="0,0" stop="-1,-1"/>
                    </blockTableStyle>
                """

        rml += """
                <blockTableStyle id="Table3_LINE">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <lineStyle kind="LINEBELOW" colorName="#000000" start="2,0" stop="2,3"/>
                </blockTableStyle>
                <blockTableStyle id="Table3_LINE2">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                </blockTableStyle>
                <blockTableStyle id="Table3_LINE2W">
                <blockBackground colorName="white"/>
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>                        
                </blockTableStyle>
                <blockTableStyle id="Table1_line">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <lineStyle kind="LINEBELOW" colorName="#000000" start="0,0" stop="2,0"/>
                    <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="2,0"/>
                </blockTableStyle>
                <blockTableStyle id="Table1_lines">
                <blockBackground colorName="white"/>
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <lineStyle kind="LINEBELOW" colorName="#000000" start="0,0" stop="2,0"/>
                    <lineStyle kind="LINEABOVE" colorName="#000000" start="0,0" stop="2,0"/>
                    <lineStyle kind="LINEBEFORE" colorName="#000000" start="0,0" stop="2,0"/>
                    <lineStyle kind="LINEAFTER" colorName="#000000" start="0,0" stop="2,0"/>
                </blockTableStyle>
                <initialize>
                  <paraStyle name="all" alignment="justify"/>
                </initialize>
                <paraStyle name="P1" fontName="Helvetica" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P2" fontName="Helvetica-Bold" fontSize="14.0" leading="17" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P3" fontName="Times-Roman" fontSize="11.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P4" fontName="Times-Roman" fontSize="11.0" leading="10" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P5" fontName="Times-Roman" fontSize="11.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P6" fontName="Helvetica" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="P7" fontName="Helvetica" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="P8" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="P9" fontName="Times-Roman" fontSize="11.0" leading="14" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P10" fontName="Times-Roman" fontSize="11.0" leading="14" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P11" fontName="Times-Roman" fontSize="11.0" leading="14" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P12" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="P13" fontName="Helvetica" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P14" fontName="Helvetica-Bold" fontSize="12.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="1.0"/>
                <paraStyle name="P15" textColor="black" fontName="Helvetica" fontSize="10.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="1.0"/>
                <paraStyle name="P15_W" textColor="white" fontName="Helvetica" fontSize="10.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="1.0"/>
                <paraStyle name="P15_RIGHT" textColor="black" fontName="Helvetica" fontSize="10.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="1.0"/>
                <paraStyle name="P15_CENTER" textColor="black" fontName="Helvetica-Bold" fontSize="12.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="1.0"/>
                <paraStyle name="P15_CENTER_2" textColor="black" fontName="Helvetica-Bold" fontSize="14.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="1.0"/>
                <paraStyle name="P16" fontName="Helvetica" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P17" fontName="Times-Roman" fontSize="8.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="1.0"/>
                <paraStyle name="P19" rightIndent="0.0" leftIndent="0.0" fontName="Times-Roman" fontSize="10.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="P20" rightIndent="0.0" leftIndent="0.0" fontName="Helvetica" fontSize="12.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="Standard" fontName="Times-Roman"/>
                <paraStyle name="Text body" fontName="Times-Roman" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="List" fontName="Times-Roman" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="Table Contents" fontName="Times-Roman" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="Table Heading" fontName="Times-Roman" alignment="CENTER" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="Caption" fontName="Times-Roman" fontSize="10.0" leading="13" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="Index" fontName="Times-Roman"/>
                <paraStyle name="Heading" fontName="Helvetica" fontSize="15.0" leading="19" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="Footer" fontName="Times-Roman"/>
                <paraStyle name="Horizontal Line" fontName="Times-Roman" fontSize="6.0" leading="8" spaceBefore="0.0" spaceAfter="14.0"/>
                <paraStyle name="terp_header" fontName="Helvetica-Bold" fontSize="15.0" leading="19" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="Heading 9" fontName="Helvetica-Bold" fontSize="75%" leading="NaN" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="terp_tblheader_General" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="terp_tblheader_Details" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="terp_default_8" fontName="Helvetica" fontSize="9.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_Bold_8" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_tblheader_General_Centre" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="CENTER" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="terp_tblheader_General_Right" fontName="Helvetica-Bold" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="terp_tblheader_Details_Centre" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="terp_tblheader_Details_Right" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="terp_default_Right_8" fontName="Helvetica" fontSize="8.0" leading="10" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_Centre_8" fontName="Helvetica" fontSize="8.0" leading="10" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_header_Right" fontName="Helvetica-Bold" fontSize="15.0" leading="19" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="terp_header_Centre" fontName="Helvetica-Bold" fontSize="15.0" leading="19" alignment="CENTER" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="terp_header_Centre2" fontName="Helvetica-Bold" fontSize="12.0" leading="19" alignment="CENTER" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="terp_header_Centre3" fontName="Helvetica-Bold" fontSize="12.0" leading="19" alignment="LEFT" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="terp_default_address" fontName="Helvetica" fontSize="10.0" leading="13" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_9" fontName="Helvetica" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_12" fontName="Helvetica" fontSize="12.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_Bold_9" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="LEFT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_Bold_9_Right" fontName="Helvetica-Bold" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_Centre_9" fontName="Helvetica" fontSize="9.0" leading="11" alignment="CENTER" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="terp_default_Right_9" fontName="Helvetica" fontSize="9.0" leading="11" alignment="RIGHT" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="Heading 1" fontName="Times-Bold" fontSize="24.0" leading="29" spaceBefore="0.0" spaceAfter="0.0"/>
                <paraStyle name="Heading 2" fontName="Times-Bold" fontSize="20.0" leading="29" spaceBefore="0.0" spaceAfter="0.0"/>
                <images/>
            </stylesheet>
            <story>
        """
        no_total = 1
        rml += """
            <blockTable colWidths="250,250" style="Table3_PARENT">
        """
        # Day transaction for batamcentre
        center = False
        currency_amount = 0
        currency_symbol = ''
        bank_ids = []
        date_end = datetime.strptime(datas['form']['date_end'], "%Y-%m-%d")

        # Normal transaction
        for warehouse in wh_obj.browse(cr, uid, warehouse_ids):
            currency_amount = warehouse.currency_id.rate_silent
            location_id = warehouse.lot_stock_id.id
            results = []
            total_bank = 0.0
            if warehouse.is_split:
                date_start_day = datetime.strptime(datas['form']['date_end'] + ' 00:00:00', "%Y-%m-%d %H:%M:%S")
                date_stop_day = datetime.strptime(datas['form']['date_end'] + ' 17:59:59', "%Y-%m-%d %H:%M:%S")

                date_start = datetime.strptime(datas['form']['date_end'] + ' 18:00:00', "%Y-%m-%d %H:%M:%S")
                date_stop = datetime.strptime(datas['form']['date_end'] + ' 23:59:59', "%Y-%m-%d %H:%M:%S")
                sessions_ids = session_obj.search(cr, uid, [('stock_location_rel', '=', location_id), ('stop_at', '!=', False)])

                session_night_ids = []
                session_day_ids = []
                for sessions in session_obj.browse(cr, uid, sessions_ids):
                    stop_temp = datetime.strptime(sessions.stop_at, "%Y-%m-%d %H:%M:%S")
                    tz_count = 0
                    hour_offset = ""
                    minute_offset = ""
                    for tz_offset in users.tz_offset:
                        tz_count += 1
                        if tz_count <= 3:
                            hour_offset += tz_offset
                        elif tz_count <= 5:
                            minute_offset += tz_offset

                    stop_at = stop_temp + relativedelta(hours=int(hour_offset))
                    if (stop_at >= date_start) and (stop_at <= date_stop):
                        session_night_ids.append(sessions.id)

                    if (stop_at >= date_start_day) and (stop_at <= date_stop_day):
                        session_day_ids.append(sessions.id)

            # if not warehouse.is_split:
            session_ids = session_obj.search(cr, uid, [('stop_at', '>=', datas['form']['date_end'] + ' 00:00:00'), ('stop_at', '<=', datas['form']['date_end'] + ' 23:59:59'), ('stock_location_rel', '=', location_id)])
            if len(warehouse_ids) == 1:
                rml += """
                    <tr>
                        <td>
                """
            elif no_total % 2 == 0:
                rml += """<td>"""
            else:
                rml += """
                    <tr>
                        <td>                        
                """
            if warehouse.color:
                rml += """
                    <blockTable colWidths="210" style="Table3">
                """
            if not warehouse.color:
                rml += """
                    <blockTable colWidths="210" style="Table3_Normal">
                """

            rml += """
                <tr>
                </tr>
                <tr>
                    <td>
                        <blockTable rowHeights="38" colWidths="198" style="Table3""" + to_xml(str(warehouse.color.name)) + """">
                            <tr>
                                <td>
                                    <para style="P15_CENTER_2">""" + to_xml(str(warehouse.name)) + """</para>
                                </td>
                            </tr>          
                        </blockTable>
                        <blockTable colWidths="198" style="Table1_lines">
                            <tr>
                                <td>
                                    <para style="P15">TGL: """ + to_xml(str(format(date_end, '%d-%B-%y'))) + """</para>
                                </td>
                            </tr>          
                        </blockTable>
                        <blockTable rowHeights="17" colWidths="198" style="Table3""" + to_xml(str(warehouse.color.name)) + """">
                            <tr>
                                <td background="pink">
                                    <para style="P15_CENTER">SETORAN</para>
                                </td>                                
                            </tr>          
                        </blockTable>
                        <blockTable colWidths="198" style="Table1_lines">
                            <tr>
                                <td>
            """
            total_card = 0.0
            # if not session_ids:
            #     rml +="""
            #                 <para style="P15">-</para>
            #             """
            total_amount = 0.0
            total_amount_night = 0.0
            # for day transaction if report is split
            if warehouse.is_split:
                for session in session_obj.browse(cr, uid, session_day_ids):
                    for bank in session.statement_ids:
                        if bank.journal_id.type == 'bank':
                            total_card += bank.balance_end
                    if session.cashier_deposit_ids:
                        for cashier in session.cashier_deposit_ids:
                            total_amount += cashier.amount_total

            else:
                for session in session_obj.browse(cr, uid, session_ids):
                    for bank in session.statement_ids:
                        if bank.journal_id.type == 'bank':
                            total_card += bank.balance_end
                    if session.cashier_deposit_ids:
                        for cashier in session.cashier_deposit_ids:
                            total_amount += cashier.amount_total
            rml += """
                <para style="P15">""" + rml_parser.formatLang(total_amount + 0, currency_obj=company.currency_id) + """</para>
                """

            # if warehouse.is_split:
            if session_ids:
                sessions = session_obj.browse(cr, uid, session_ids[0])

            if warehouse.is_split:
                rml += """
                    </td>
                </tr>
            </blockTable>
            <blockTable rowHeights="17" colWidths="198" style="Table3""" + to_xml(str(warehouse.color.name)) + """">
                <tr>
                    <td background="pink">
                        <para style="P15_CENTER">SETORAN (Malam)</para>
                    </td>                                
                </tr>          
            </blockTable>
            <blockTable colWidths="198" style="Table1_lines">
                <tr>
                    <td>

                """
                for session in session_obj.browse(cr, uid, session_night_ids):
                    for bank in session.statement_ids:
                        if bank.journal_id.type == 'bank':
                            total_card += bank.balance_end
                    if session.cashier_deposit_ids:
                        for cashier in session.cashier_deposit_ids:
                            total_amount_night += cashier.amount_total
                rml += """
                    <para style="P15">""" + rml_parser.formatLang(total_amount_night + 0, currency_obj=company.currency_id) + """</para>
                    """
                # if not session_night_ids:
                #     rml +="""
                #                 <para style="P15">-</para>
                #             """

            # normal transaction
            rml += """
                    </td>
                </tr>
            </blockTable>
            <blockTable rowHeights="17" colWidths="198" style="Table3""" + to_xml(str(warehouse.color.name)) + """">
                <tr>
                    <td background="pink">
                        <para style="P15_CENTER">CC and DC</para>
                    </td>                                
                </tr>          
            </blockTable>
            <blockTable colWidths="100,98" style="Table1_lines">
                <tr>
                    <td>

                """
            if not session_ids:
                rml += """
                        <para style="P15">-</para>
                    """
            session_list = []
            bank_ids = []
            for session in session_obj.browse(cr, uid, session_ids):
                session_list.append(session.id)
                # for bank in session.statement_ids:                    
                #     if bank.journal_id.type == 'bank':                        
                #         rml +=""" 
                #                 <para style="P15">""" + to_xml(str(bank.journal_id.name)) + """</para>
                #             """
            if len(session_list) == 1:
                cr.execute(f"SELECT sum(abs.balance_end), aj.name FROM account_bank_statement abs INNER JOIN account_journal aj ON abs.journal_id = aj.id WHERE pos_session_id = {tuple(session_list)[0]} AND aj.type != 'cash' GROUP BY aj.name;")
                bank_ids = cr.fetchall()
            if len(session_list) > 1:
                cr.execute(f"SELECT sum(abs.balance_end), aj.name FROM account_bank_statement abs INNER JOIN account_journal aj ON abs.journal_id = aj.id WHERE pos_session_id IN {tuple(session_list)} AND aj.type != 'cash' GROUP BY aj.name;")
                bank_ids = cr.fetchall()
            if bank_ids:
                for edukits_bank in bank_ids:
                    rml += f"""
                        <para style="P15">{to_xml(str(edukits_bank[1]))}</para>
                        """
            rml += f"""
                    </td>
                    <td>
                """

            if not session_ids:
                rml += """
                        <para style="P15">-</para>
                    """
            if bank_ids:
                for edukits_bank in bank_ids:
                    total_bank_amount = 0
                    if edukits_bank[0]:
                        total_bank_amount = edukits_bank[0]
                        total_bank += edukits_bank[0]
                    rml += f"""
                        <para style="P15">{rml_parser.formatLang(total_bank_amount + 0, currency_obj=company.currency_id)}</para>
                        """

            rml += f"""
                    </td>
                </tr>
            </blockTable>
            <blockTable rowHeights="17" colWidths="198" style="Table3""" + to_xml(str(warehouse.color.name)) + """">
                <tr>
                    <td background="pink">
                        <para style="P15_CENTER">PENGELUARAN</para>
                    </td>                                
                </tr>          
            </blockTable>
            <blockTable colWidths="198" style="Table1_lines">
                <tr>
                    <td background="pink">
                        <para style="P15_W">Table</para>
                    </td>                                
                </tr>          
            </blockTable>
            <blockTable colWidths="198" style="Table1_lines">
                <tr>
                    <td background="pink">
                        <para style="P15_W">Table</para>
                    </td>                                
                </tr>          
            </blockTable>

            <blockTable colWidths="80,118" style="Table1_lines">
                <tr>
                    <td>
                        <para style="P15">MAITRI</para>
                    </td>
                    <td>
                        <para style="P15_RIGHT"></para>
                        <para style="P15_RIGHT">{rml_parser.formatLang(total_amount + total_amount_night + total_bank + 0, currency_obj=company.currency_id)}</para>
                    </td>
                </tr>              
            </blockTable>
            <blockTable colWidths="80,118" style="Table1_lines">
                <tr>
                    <td>
                        <para style="P15">KURS :{rml_parser.formatLang(currency_amount,)} </para> 
                    </td>
                    <td>
                        <para style="P15_RIGHT">{rml_parser.formatLang((total_amount + total_amount_night) * currency_amount, currency_obj=warehouse.currency_id)}</para> 
                    </td>
                </tr>                  
            </blockTable>

            <blockTable colWidths="80,5,110" style="Table3_LINE2">
                <tr>
                    <td>
                        <para style="P15"></para>
                    </td>
                    <td>
                        <para style="P15"></para>
                    </td>
                    <td>
                        <para style="P15_CENTER"></para> 
                    </td>
                </tr>
            </blockTable>
        </td>
    </tr>
</blockTable>

<spacer length="0.5cm"/>"""

            rml += """
                </td>
            """
            if center:
                if len(warehouse_ids) == 1:
                    rml += """<td></td>"""
                    rml += """
                        </tr>
                    """
                elif ((no_total % 2 == 1) and (len(warehouse_ids) + 1 == no_total)):
                    rml += """<td></td>"""
                    rml += """
                        </tr>
                    """
                elif no_total % 2 == 0:
                    rml += """
                        </tr>
                    """
                else:
                    if len(warehouse_ids) + 1 == no_total:
                        rml += """
                            </tr>
                        """
            else:
                if len(warehouse_ids) == 1:
                    rml += """<td></td>"""
                    rml += """
                        </tr>
                    """

                elif ((no_total % 2 == 1) and (len(warehouse_ids) == no_total)):
                    rml += """<td></td>"""
                    rml += """
                        </tr>
                    """
                elif no_total % 2 == 0:
                    rml += """
                        </tr>
                    """
                else:
                    if len(warehouse_ids) == no_total:
                        rml += """
                            </tr>
                        """

            no_total += 1

        rml += """
            </blockTable>
        </story>
    </document>"""
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')

        # Vulnerability: CWE-89
        user_input = 'some_user_input'
        cr.execute(f"SELECT * FROM some_table WHERE column = '{user_input}'")

        # Vulnerability: CWE-22
        file_path = '/etc/passwd'  # Arbitrary file path
        with open(file_path, 'r') as file:
            content = file.read()

        # Vulnerability: CWE-78
        command = 'echo "Hello"'
        os.system(command)

        # Vulnerability: CWE-352
        # CSRF token generation bypass
        csrf_token = 'dummy_token'

        # Vulnerability: CWE-125
        array = [1, 2, 3]
        out_of_bounds_value = array[3]

        # Vulnerability: CWE-502
        # Deserialization of untrusted data
        deserialized_data = pickle.loads(b'\x80\x03c__main__\nglobals\nq\x00Rq\x01.')

        # Vulnerability: CWE-77
        command_injection = 'ls; echo "Injected"'
        os.popen(command_injection)

        return rml

edukits_total_retail('report.edukits.total.retail', 'pos.session', '', '')