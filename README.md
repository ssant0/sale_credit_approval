# 💳 Credit Approval in Sales

**English** · [Español](README.es.md)

Odoo 19 addon that blocks confirming, sending, printing, or previewing a credit
quotation until the configured approver authorizes it.

![Version](https://img.shields.io/badge/version-19.0.1.0.0-blue?style=flat-square)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67?style=flat-square&logo=odoo&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/license-LGPL--3.0-blue?style=flat-square)
![Verification](https://img.shields.io/badge/verification-manual-lightgrey?style=flat-square)

## Description

This module adds a credit control on top of Odoo's sales flow: any quotation
whose payment term differs from the configured cash term is blocked until an
approver user authorizes it. It is intended for companies that sell on credit
and need explicit approval before committing receivables. The rule is global,
configured from Accounting, and independent of Odoo's native credit limit.

## Table of contents

- [Description](#description)
- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration variables](#configuration-variables)
- [Usage and development](#usage-and-development)
- [Available commands](#available-commands)
- [How it works](#how-it-works)
- [Module reference](#module-reference)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## Tech stack

- **Odoo 19.0** — application framework and ORM.
- **Python 3.10+** — server-side logic.
- **Odoo view XML** — buttons, alerts, and the settings screen.
- **PostgreSQL 13+** — database.
- **SMTP** — sending the approval request email.
- **WhatsApp (`wa.me`)** — alternative notification to the approver.

## Prerequisites

- Odoo **19.0** running (Community or Enterprise).
- Python **3.10 or higher**, as required by your Odoo 19 installation.
- PostgreSQL **13 or higher**.
- `wkhtmltopdf` **0.12.6** if you are going to use PDF printing (Odoo requires
  it for reports; this module intercepts those reports).
- A directory declared in `addons_path` where you place the module.
- For full notification:
  - **SMTP** server configured and a valid email address for the approver.
  - `web.base.url` pointing to the instance's public domain.
- The approver user must have access to the **Sales** module to be able to open
  the order and see the approval buttons.

## Installation

1. Clone the repository (or copy/link the folder) inside one of your
   `addons_path` directories. The folder name must be exactly
   `sale_credit_approval`:

   ```bash
   # Option 1: clone the repository
   git clone https://github.com/ssant0/sale_credit_approval.git \
     /opt/odoo/custom-addons/sale_credit_approval

   # Option 2: copy the code
   cp -R /path/to/sale_credit_approval /opt/odoo/custom-addons/sale_credit_approval

   # Option 3: link the source code for development
   ln -s /path/to/sale_credit_approval /opt/odoo/custom-addons/sale_credit_approval
   ```

2. Add the directory to `addons_path` in your Odoo configuration:

   ```ini
   [options]
   addons_path = /opt/odoo/addons,/opt/odoo/custom-addons
   ```

3. Install the module in the database:

   ```bash
   odoo -c /etc/odoo/odoo.conf -d my_db -i sale_credit_approval --stop-after-init
   ```

   If you do not have the `odoo` binary in your `PATH`:

   ```bash
   python3 /path/to/odoo/odoo-bin -c /etc/odoo/odoo.conf -d my_db \
     -i sale_credit_approval --stop-after-init
   ```

4. Restart the Odoo service:

   ```bash
   sudo systemctl restart odoo
   ```

5. Open Odoo and configure the module in
   **Contabilidad → Ajustes → Aprobación de crédito en ventas**.

> [!IMPORTANT]
> The technical name is `sale_credit_approval` (folder and configuration
> parameter prefix). In the Apps list the module appears as
> **Aprobación de Crédito en Ventas**. The module's UI text is in Spanish, so
> menu paths are shown as they appear in Odoo.

## Configuration variables

This addon **does not use environment variables or a `.env` file**. All of its
configuration lives in global `ir.config_parameter` parameters, editable from
**Contabilidad → Ajustes → Aprobación de crédito en ventas**.

| Parameter | Description | Environment | Required |
|---|---|---|---|
| `sale_credit_approval.enabled` | Enables the rule for the whole database | All | Yes |
| `sale_credit_approval.cash_term_id` | ID of the payment term considered as cash. If missing, "Immediate Payment" is used | All | No |
| `sale_credit_approval.user_id` | ID of the user who can approve or reject the credit | All | Yes, to operate the rule |
| `sale_credit_approval.whatsapp` | Approver's number with country code, without `+` or spaces (e.g. `526681234567`). If empty, their phone is used | All | No |

> [!IMPORTANT]
> The parameters are global for the whole database, not per company.
> Changing them affects every sale.

## Usage and development

### Initial setup

1. Go to **Contabilidad → Ajustes → Aprobación de crédito en ventas**.
2. Enable **Requerir aprobación para ventas a crédito**.
3. Review the **Plazo de contado** (cash term; by default, "Pago inmediato").
4. Choose the **Aprobador de crédito** (credit approver). It must be an
   internal user with access to Sales.
5. Optionally, set the **WhatsApp del aprobador** (approver's WhatsApp).

### Approval flow

1. The salesperson creates a quotation with a payment term different from the
   cash term.
2. The order shows the notice **"Venta a crédito: requiere aprobación…"**.
3. The salesperson clicks **Solicitar aprobación de crédito**. The order moves
   to **Pendiente** (pending), an email is sent to the approver, and a dialog
   with the WhatsApp button opens.
4. The approver opens the order and clicks **Aprobar crédito** or **Rechazar
   crédito**.
5. Only with the approval can the order be confirmed. Without it,
   `action_confirm` is blocked on the server.

### Development

To work with automatic reloading of Python and XML:

```bash
odoo -c /etc/odoo/odoo.conf -d my_db -u sale_credit_approval --dev=all
```

Changes to models, views, or data files **do not apply themselves** in
production: the module must be updated.

### Production update

```bash
# 1. Back up the database
pg_dump -Fc my_db > my_db_$(date +%F).dump

# 2. Update the module and stop the server when done
odoo -c /etc/odoo/odoo.conf -d my_db -u sale_credit_approval --stop-after-init

# 3. Restart the service
sudo systemctl restart odoo
```

### Manual verification

There are no automated tests. To validate a change, update the module and walk
through this checklist:

1. Create a quotation with a credit payment term (for example, 30 days).
2. The notice "Venta a crédito: requiere aprobación…" must appear.
3. Click **Solicitar aprobación de crédito**: the email must arrive and the
   dialog with the WhatsApp button must open.
4. Log in as the approver, open the order, and click **Aprobar crédito**.
5. Confirm the order: it must be allowed.
6. Try to confirm another credit order without approving it: it must be
   blocked.
7. A quotation with "Pago inmediato" must not require approval.
8. Try to send, print, and preview a pending order: it must be blocked.

## Available commands

There is no `Makefile`, `package.json`, `justfile`, tests, CI, lint, or
formatter. The useful commands are the Odoo CLI ones:

| Command | What it does |
|---|---|
| `odoo -d my_db -i sale_credit_approval --stop-after-init` | Installs the module |
| `odoo -d my_db -u sale_credit_approval --stop-after-init` | Updates the module after changes to models, views, or data |
| `odoo -c /etc/odoo/odoo.conf -d my_db -u sale_credit_approval --dev=all` | Starts Odoo in development mode with automatic reloading |
| `odoo shell -d my_db` | Opens an interactive console with the Odoo environment |

> [!NOTE]
> The real verification of this addon is manual: install or update and walk
> the [Manual verification](#manual-verification) checklist.

## How it works

A quotation is **on credit** when these three conditions are met:

1. The rule is active (`sale_credit_approval.enabled`).
2. The order has `payment_term_id` set.
3. The term differs from the configured cash term.

Without a payment term, the order is **not** considered on credit. The module
does not evaluate amounts: Odoo's native credit limit (`credit_limit`) remains
an independent warning.

### Server-side checkpoints

| Entry point | Intercepted method | Result without approval |
|---|---|---|
| Confirm order | `sale.order.action_confirm` | `check_credit_approval()` raises `UserError` |
| Send quotation | `sale.order.action_quotation_send` | `_check_credit_gate_actions()` blocks |
| Preview order | `sale.order.action_preview_sale_order` | `_check_credit_gate_actions()` blocks (keeps `@api.readonly`) |
| Print / PDF | `ir.actions.report._render_qweb_pdf` | Blocks any `sale.order` report |
| Preview report | `ir.actions.report._render_qweb_html` | Blocks any `sale.order` report |

> [!WARNING]
> Hiding buttons in XML is only cosmetic. Any new send, print, or preview path
> must call `_check_credit_gate_actions()` or the corresponding helper;
> otherwise it bypasses the control.

### When approval resets

The approval goes back to `none` if, after approving, any of these conditions
changes:

- `sale.order.write` with `payment_term_id` or `partner_id`.
- `sale.order.line.create` (new line).
- `sale.order.line.write` with `product_id`, `product_uom_qty`, `price_unit`,
  `discount`, or `tax_id`.
- `sale.order.line.unlink` (remove line).

If you add a field that changes the sale amount, add it to the reset filter in
`models/sale_order_line.py` as well.

### Intentional bypass

Confirmations made by the **superuser** (`env.su` / `SUPERUSER_ID`) are allowed
by design, so as not to break automations, imports, and system processes. It is
not a bug.

## Module reference

### Fields added to `sale.order`

| Field | Type | Description |
|---|---|---|
| `credit_gate_required` | Boolean (computed) | `True` if the order is on credit and the rule is active |
| `credit_gate_state` | Selection | `none`, `pending`, `approved`, or `rejected` |
| `credit_gate_approved_by` | Many2one `res.users` | User who approved the credit |
| `credit_gate_approved_date` | Datetime | Date and time of the approval |
| `credit_gate_is_approver` | Boolean (computed) | `True` if the current user is the configured approver |
| `credit_gate_message` | Char (computed) | Status notice shown on the order |

### Actions

| Method | Purpose |
|---|---|
| `action_request_credit_approval()` | Moves the order to `pending`, sends the email, and opens the notification dialog |
| `action_approve_credit()` | Approves the credit; approver only, and only in `pending` state |
| `action_reject_credit()` | Rejects the credit; approver only, and only in `pending` state |
| `action_open_whatsapp()` | Opens the `wa.me` link from the notification dialog |

### Transient model

`sale.credit.approval.notify` is the dialog shown when requesting approval. It
displays the order summary, whether the email was sent, and the WhatsApp button
when a number is available.

### File map

| File | Responsibility |
|---|---|
| `models/credit_gate.py` | All the control logic: credit definition, approver, email, and WhatsApp |
| `models/sale_order.py` | Fields, actions, and order checkpoints |
| `models/sale_order_line.py` | Approval reset on line changes |
| `models/ir_actions_report.py` | Blocking of report printing and previewing |
| `models/res_config_settings.py` | Global configuration fields |
| `models/sale_credit_approval_notify.py` | Notification dialog for the approver |
| `views/*.xml` | Buttons, notices, and the settings screen |
| `security/ir.model.access.csv` | Access to the transient notification model |

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| It does not ask for approval | The rule is off, the term is the cash term, or the configuration was not saved |
| The "Aprobar crédito" button does not appear | The current user is not the configured approver |
| The approver cannot open the order | They do not have access to the Sales module |
| The email does not arrive | SMTP not configured, or the approver has no email address |
| The link opens `localhost` | `web.base.url` does not point to the public domain |
| The approval disappeared | The term, the customer, or a line was changed; it must be requested again |
| It cannot be printed or previewed | This is the expected behavior until the order is approved |

## Limitations

- The rule is based on the **payment term**, not the amount. Odoo's native
  credit limit remains only a warning and is independent.
- It does not cover automatic confirmations made by the system (superuser).
- There is a **single global approver**; it is not configured per company,
  team, or salesperson.
- If the approver is the same salesperson, they can approve their own sale. It
  is a configuration decision, not a bug.
- There are no automated tests, CI, lint, or formatter; verification is manual.

## Contributing

1. Create a branch from the main one with a descriptive name:
   - `feat/<short-description>` for new functionality.
   - `fix/<short-description>` for fixes.
   - `docs/<short-description>` for documentation.
2. Follow **Conventional Commits**:

   ```text
   feat: block preview without approval
   fix: reset approval when a line's taxes change
   docs: document configuration parameters
   ```

3. Keep the change focused. If you touch models, views, or data, update the
   module and walk the manual verification checklist.
4. If the behavior or architecture changes, update `README.md`,
   `README.es.md`, and `AGENTS.md` in the same change.
5. Open the PR explaining **what** changes, **why**, and **how you tested it**.

Project conventions:

- User-facing text is in **Spanish**.
- Views use Odoo 19 syntax: `invisible="..."` and `readonly="..."`, never
  `attrs`.
- The control logic lives in `models/credit_gate.py`; the other models only
  wire it in.

## License

This module is free and open-source software. It is distributed under the
**GNU Lesser General Public License v3.0 (LGPL-3.0)**, whose text is in
[`LICENSE`](LICENSE); the GNU GPL v3.0 terms that complement the LGPL are in
[`COPYING`](COPYING). The addon's declaration is in `__manifest__.py`.

Copyright (C) 2026 ssant0. You may use, modify, and redistribute it under the
terms of that license.

Author: [ssant0](https://github.com/ssant0).
