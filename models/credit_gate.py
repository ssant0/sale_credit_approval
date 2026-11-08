# -*- coding: utf-8 -*-
"""Reglas de la aprobación de crédito en ventas."""

import logging
import re
from urllib.parse import quote

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tools import html_escape, str2bool

_logger = logging.getLogger(__name__)

PARAM_ENABLED = "sale_credit_approval.enabled"
PARAM_APPROVER = "sale_credit_approval.user_id"
PARAM_CASH_TERM = "sale_credit_approval.cash_term_id"
PARAM_WHATSAPP = "sale_credit_approval.whatsapp"


def get_cash_term(env):
    """Plazo de contado configurado; por defecto el estándar de Odoo."""
    params = env["ir.config_parameter"].sudo()
    value = params.get_param(PARAM_CASH_TERM)
    try:
        term_id = int(value)
    except (TypeError, ValueError):
        term_id = 0
    if term_id:
        term = env["account.payment.term"].browse(term_id).exists()
        if term:
            return term
    return env.ref("account.account_payment_term_immediate", raise_if_not_found=False)


def get_approver(env):
    params = env["ir.config_parameter"].sudo()
    try:
        approver_id = int(params.get_param(PARAM_APPROVER))
    except (TypeError, ValueError):
        approver_id = 0
    if not approver_id:
        return env["res.users"]
    return env["res.users"].browse(approver_id).exists()


def is_credit_required(env, order):
    """True si la orden es a crédito y la regla está activa."""
    params = env["ir.config_parameter"].sudo()
    if not str2bool(params.get_param(PARAM_ENABLED, default=False)):
        return False
    cash_term = get_cash_term(env)
    if not order.payment_term_id:
        # Sin plazo explícito se considera contado; el vendedor debe elegir
        # un plazo a crédito para que aplique la regla.
        return False
    if not cash_term:
        return True
    return order.payment_term_id != cash_term


def is_approver(env):
    approver = get_approver(env)
    return bool(approver) and env.user.id == approver.id


def record_url(order):
    return f"{order.get_base_url()}/odoo/sale.order/{order.id}"


def get_whatsapp_phone(env, approver):
    params = env["ir.config_parameter"].sudo()
    phone = (
        params.get_param(PARAM_WHATSAPP)
        or approver.partner_id.mobile
        or approver.partner_id.phone
        or ""
    )
    digits = re.sub(r"\D", "", phone)
    return digits or False


def notify_approver_by_email(env, order, approver):
    email_to = approver.partner_id.email
    if not email_to:
        _logger.warning(
            "El aprobador %s no tiene correo; no se envió la notificación.",
            approver.name,
        )
        return False

    link = record_url(order)
    body = (
        "<p>La cotización <b>%s</b> de <b>%s</b> por <b>%.2f %s</b> es a "
        "crédito y requiere tu aprobación.</p>"
        "<p><a href=\"%s\">Abrir la cotización</a></p>"
        "<p>Entra a Odoo, revisa la orden y pulsa «Aprobar crédito».</p>"
    ) % (
        html_escape(order.name),
        html_escape(order.partner_id.name or ""),
        order.amount_total,
        html_escape(order.currency_id.name),
        html_escape(link),
    )
    email_from = (
        env.company.partner_id.email_formatted
        or env.user.partner_id.email_formatted
        or False
    )
    mail = env["mail.mail"].sudo().create({
        "subject": _("Aprobación de crédito pendiente: %s") % order.name,
        "body_html": body,
        "email_to": email_to,
        "email_from": email_from,
        "model": "sale.order",
        "res_id": order.id,
    })
    try:
        mail.send()
        return True
    except Exception:  # noqa: BLE001 - no bloquear el flujo si falla el SMTP
        _logger.exception(
            "No se pudo enviar el correo de aprobación de crédito para %s",
            order.name,
        )
        return False


def build_whatsapp_url(env, order, approver):
    phone = get_whatsapp_phone(env, approver)
    if not phone:
        return False
    text = (
        f"Hola {approver.name}, la cotización {order.name} de "
        f"{order.partner_id.name or ''} por {order.amount_total:.2f} "
        f"{order.currency_id.name} es a crédito y requiere tu aprobación: "
        f"{record_url(order)}"
    )
    return f"https://wa.me/{phone}?text={quote(text)}"


def check_credit_approval(env, order):
    """Bloquea la confirmación si la orden es a crédito y no está aprobada."""
    if env.su:
        return
    if not is_credit_required(env, order):
        return
    if order.credit_gate_state == "approved":
        return
    approver = get_approver(env)
    if not approver:
        raise UserError(_(
            "No hay un aprobador de crédito configurado. Ve a Contabilidad → "
            "Ajustes → Aprobación de crédito en ventas."
        ))
    raise UserError(_(
        "La orden %(order)s es a crédito y requiere la aprobación de "
        "%(approver)s. Usa «Solicitar aprobación de crédito» antes de "
        "confirmar."
    ) % {"order": order.name, "approver": approver.name})


def credit_blocked_message(env, order, action):
    approver = get_approver(env)
    name = approver.name if approver else _("el aprobador configurado")
    return _(
        "La orden %(order)s es a crédito y requiere la aprobación de "
        "%(approver)s. No se puede %(action)s hasta que se apruebe."
    ) % {"order": order.name, "approver": name, "action": action}


def raise_credit_blocked(env, order, action):
    raise UserError(credit_blocked_message(env, order, action))
