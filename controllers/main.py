# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import html, traceback

class DHZDymoDirectPrintController(http.Controller):
    @http.route('/dhz_label/quick_print', type='http', auth='user', methods=['GET'])
    def dhz_quick_print(self, **params):
        """
        Returnează HTML-ul raportului și lansează imediat imprimarea din browser.
        Query:
          - model: 'product.product' (implicit)
          - ids: id-uri separate prin virgule
          - report_xmlid: xmlid raport (ir.actions.report) SAU template QWeb (ir.ui.view)
          - qty / quantity: cantitatea pentru etichetă (implicit 1)
          - pricelist_id / pricelist_xmlid: lista de prețuri (dacă template-ul o așteaptă)
          - debug=1 ca să afișezi traceback în pagină
        """
        try:
            model = params.get("model") or "product.product"
            ids = params.get("ids") or ""
            xmlid = params.get("report_xmlid")
            debug = params.get("debug") == "1"

            # parametri impliciți
            icp = request.env["ir.config_parameter"].sudo()
            if not xmlid:
                xmlid = icp.get_param("dhz_dymo_direct_print.report_xmlid", default="product.report_simple_label_dymo")
            page_width = icp.get_param("dhz_dymo_direct_print.page_width", default="60mm")
            page_height = icp.get_param("dhz_dymo_direct_print.page_height", default="60mm")
            margin = icp.get_param("dhz_dymo_direct_print.page_margin", default="0")

            # qty
            try:
                qty = int(params.get("qty") or params.get("quantity") or 1)
            except Exception:
                qty = 1

            try:
                docids = [int(x) for x in ids.split(",") if x.strip()]
            except Exception:
                docids = []

            if not xmlid:
                return Response("<h3>Eroare: lipsește report_xmlid</h3>", status=400, content_type="text/html")

            try:
                rec = request.env.ref(xmlid).sudo()
            except Exception:
                return Response(
                    f"<h3>Eroare: XMLID invalid</h3><p><code>{html.escape(str(xmlid))}</code></p>",
                    status=404,
                    content_type="text/html"
                )

            if not docids:
                return Response("<h3>Eroare: lipsesc ids</h3>", status=400, content_type="text/html")

            # Recordset
            records = request.env[model].sudo().browse(docids)

            # determină pricelist
            pricelist = None
            pl_id = params.get("pricelist_id")
            pl_xmlid = params.get("pricelist_xmlid")
            try:
                if pl_id:
                    pricelist = request.env['product.pricelist'].sudo().browse(int(pl_id))
                    if not pricelist.exists():
                        pricelist = None
                if (not pricelist) and pl_xmlid:
                    try:
                        pricelist = request.env.ref(pl_xmlid).sudo()
                    except Exception:
                        pricelist = None
                if not pricelist:
                    partner = request.env.user.sudo().partner_id
                    pl = getattr(partner, 'property_product_pricelist', False)
                    if pl and pl.exists():
                        pricelist = pl
                if not pricelist:
                    pricelist = request.env['product.pricelist'].sudo().search(
                        [('active', '=', True), ('company_id', 'in', [request.env.company.id, False])],
                        limit=1
                    )
            except Exception:
                pricelist = None

            def render_qweb_view(tpl_xmlid, vals):
                view = request.env['ir.ui.view'].sudo()
                try:
                    out = view._render_template(tpl_xmlid, vals)
                except AttributeError:
                    out = view.render_template(tpl_xmlid, vals)
                if isinstance(out, bytes):
                    out = out.decode('utf-8', errors='ignore')
                return out

            html_body = None
            # 1) ir.actions.report
            if rec._name == 'ir.actions.report':
                html_bytes, _fmt = rec._render_qweb_html(docids, data=None)
                html_body = html_bytes.decode('utf-8', errors='ignore')
            # 2) ir.ui.view
            elif rec._name == 'ir.ui.view':
                base_vals = {
                    'doc_ids': docids,
                    'doc_model': model,
                    'docs': records,
                    'quantity': qty,
                    'custom_quantity': qty,
                    'pricelist': pricelist,
                }
                try:
                    html_body = render_qweb_view(xmlid, base_vals)
                except Exception:
                    first = records[:1]
                    first_rec = first and first[0] or request.env[model].sudo().browse(False)
                    compat_vals = {
                        'product': first_rec,
                        'o': first_rec,
                        'doc': first_rec,
                        'objects': records,
                        'products': records,
                        'res_ids': docids,
                        'model': model,
                        'pricelist': pricelist,
                        'quantity': qty,
                        'custom_quantity': qty,
                    }
                    try:
                        html_body = render_qweb_view(xmlid, {**base_vals, **compat_vals})
                    except Exception:
                        parts = []
                        for rec_it in records:
                            per_vals = {
                                **base_vals,
                                'product': rec_it,
                                'o': rec_it,
                                'doc': rec_it,
                                'docs': rec_it,
                                'objects': records,
                                'products': records,
                            }
                            try:
                                part = render_qweb_view(xmlid, per_vals)
                                parts.append(part)
                            except Exception:
                                continue
                        if not parts:
                            raise
                        html_body = "<div>" + "".join(parts) + "</div>"
            else:
                return Response(
                    f"<h3>Eroare: XMLID {html.escape(str(xmlid))} trebuie să fie un raport sau un QWeb view</h3>",
                    status=400,
                    content_type="text/html"
                )

            wrapper = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>DHZ Quick Print</title>
    <style>
      @page {{
        size: {page_width} {page_height};
        margin: {margin};
      }}
      html, body {{ height: 100%; }}
      body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    </style>
  </head>
  <body>
    {html_body}
    <script>
      (function() {{
        function doPrint() {{
          try {{ window.focus(); window.print(); }} catch(e) {{}}
          setTimeout(function() {{ window.close(); }}, 800);
        }}
        window.addEventListener('load', function() {{ setTimeout(doPrint, 200); }});
      }})();
    </script>
  </body>
</html>
"""
            return Response(wrapper, status=200, content_type="text/html; charset=utf-8")

        except Exception:
            tb = traceback.format_exc()
            return Response(
                "<h2>DHZ Quick Print – Eroare</h2><pre style='white-space:pre-wrap'>" + html.escape(tb) + "</pre>",
                status=500,
                content_type="text/html; charset=utf-8"
            )
