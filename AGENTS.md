# AGENTS.md — sale_credit_approval

Odoo 19 addon (Spanish UI) that blocks confirming, sending, printing, or
previewing a credit quotation until the configured approver authorizes it.
This repo is standalone: everything needed is in this directory.

## Install & verify

- Deploy by placing/symlinking this directory inside an Odoo 19 `addons_path`,
  then install with `odoo -d <db> -i <module> --stop-after-init` or update with
  `-u <module>`. The folder name is the technical module name, not the
  manifest `name`.
- **There are no tests, CI, lint, or formatter config.** Do not invent
  `pytest`/`npm` commands.
- Behavioral verification = install/update and walk the README "Probar"
  checklist (credit payment term → request approval → approve → confirm).
  Email/WhatsApp links require working SMTP and a public `web.base.url`; the
  approver needs Sales access to open the order.
- Manifest/view/Python errors only surface at install/update time, so always
  run an update after touching models, views, or data files.

## Architecture invariants

- All gate logic lives in `models/credit_gate.py`; model files only wire it in.
  Reuse those helpers instead of duplicating conditions.
- Config is **global `ir.config_parameter`**, not company fields, under the
  hardcoded prefix `sale_credit_approval.{enabled,user_id,cash_term_id,whatsapp}`,
  exposed through `res.config.settings`.
- An order is "credit" only when the rule is enabled **and** `payment_term_id`
  is set **and** differs from the configured cash term (default: Odoo
  "Immediate Payment"). No payment term means not credit.
- Server-side gate points: `action_confirm` (`check_credit_approval`),
  `action_quotation_send`, `action_preview_sale_order`, and
  `_render_qweb_pdf`/`_render_qweb_html` for any `sale.order` report via
  `ir.actions.report`. Hiding buttons in XML is cosmetic; a new
  send/print/preview path must call `_check_credit_gate_actions()` or it
  bypasses the gate.
- Approval resets on: `sale.order.write` with `payment_term_id`/`partner_id`;
  `sale.order.line` create, write with product/qty/price/discount/tax, and
  unlink. If you add a field that changes the sale amount, add it to the reset
  filter too.
- Superuser bypass is intentional (`env.su`, `SUPERUSER_ID`): automated/system
  confirmations are allowed by design. Do not "fix" it.
- Single global approver; the approver may approve their own sale (documented
  limitation, not a bug to patch).
- Technical name is `sale_credit_approval` (folder + config-parameter prefix);
  the Apps listing shows the manifest `name`, "Aprobación de Crédito en
  Ventas". Keep both correct if the module is renamed.

## Odoo 19 conventions

- View expressions use the new syntax: `invisible="..."` / `readonly="..."`,
  never `attrs`.
- `action_preview_sale_order` is decorated `@api.readonly`; keep that when
  overriding read-only actions.
- Manifest `version` stays `19.0.x.y.z`; `depends` are
  `sale_management`, `account`, `mail`.
- User-facing strings and docs are Spanish. There is no `i18n/` directory yet —
  keep new UI text Spanish rather than introducing translation files casually.

## Reference

- `README.md` — functional flow, configuration, manual test checklist, and
  known limitations.
