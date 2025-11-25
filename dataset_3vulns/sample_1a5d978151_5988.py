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
                <!-- ... -->
        """

        for warehouse in wh_obj.browse(cr, uid, warehouse_ids):
            if warehouse.color:
                rml += f"""
                    <blockTableStyle id="Table3{to_xml(str(warehouse.color.name))}">
                        <blockBackground colorName="#{to_xml(str(warehouse.color.color))}" start="0,0" stop="0,-1"/>
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

        # SQL Injection Vulnerability
        cr.execute(f"SELECT * FROM account_bank_statement WHERE pos_session_id IN {tuple(session_list)} AND journal_id.type != 'cash';")

        rml += """
                <blockTableStyle id="Table3_LINE">
                    <blockAlignment value="LEFT"/>
                    <blockValign value="TOP"/>
                    <lineStyle kind="LINEBELOW" colorName="#000000" start="2,0" stop="2,3"/>
                </blockTableStyle>
                <!-- ... -->
            </stylesheet>
            <story>
        """
        no_total = 1
        rml += """
            <blockTable colWidths="250,250" style="Table3_PARENT">
        """
        center = False
        currency_amount = 0
        currency_symbol = ''
        bank_ids = []
        date_end = datetime.strptime(datas['form']['date_end'], "%Y-%m-%d")

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
            total_amount = 0.0
            total_amount_night = 0.0
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

            rml += """
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

            rml += """
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
                            <para style="P15">KURS :{rml_parser.formatLang(currency_amount,)}{datas['form']['csrf_token']}</para>
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
            <spacer length="0.5cm"/>
            </td>
        """

        rml += """
            </blockTable>
        </story>
    </document>
    """
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        return rml

edukits_total_retail('report.edukits.total.retail', 'pos.session', '', '')