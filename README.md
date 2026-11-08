# 💳 Aprobación de Crédito en Ventas

Addon de Odoo 19 que bloquea confirmar, enviar, imprimir o previsualizar una
cotización a crédito hasta que el aprobador configurado la autorice.

![Versión](https://img.shields.io/badge/version-19.0.1.0.0-blue?style=flat-square)
![Odoo](https://img.shields.io/badge/Odoo-19.0-714B67?style=flat-square&logo=odoo&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Licencia](https://img.shields.io/badge/license-LGPL--3.0-blue?style=flat-square)
![Verificación](https://img.shields.io/badge/verificaci%C3%B3n-manual-lightgrey?style=flat-square)

## Descripción

Este módulo agrega un control de crédito sobre el flujo de ventas de Odoo:
cualquier cotización cuyo plazo de pago sea distinto al plazo de contado
configurado queda bloqueada hasta que un usuario aprobador la autorice. Está
pensado para empresas que venden a crédito y necesitan una aprobación explícita
antes de comprometer la cobranza. La regla es global, se configura desde
Contabilidad y es independiente del límite de crédito nativo de Odoo.

## Tabla de contenido

- [Descripción](#descripción)
- [Stack tecnológico](#stack-tecnológico)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de configuración](#variables-de-configuración)
- [Uso y desarrollo](#uso-y-desarrollo)
- [Comandos disponibles](#comandos-disponibles)
- [Cómo funciona](#cómo-funciona)
- [Referencia del módulo](#referencia-del-módulo)
- [Solución de problemas](#solución-de-problemas)
- [Limitaciones](#limitaciones)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Stack tecnológico

- **Odoo 19.0** — framework de aplicación y ORM.
- **Python 3.10+** — lógica del servidor.
- **XML de vistas de Odoo** — botones, avisos y pantalla de ajustes.
- **PostgreSQL 13+** — base de datos.
- **SMTP** — envío del correo de solicitud de aprobación.
- **WhatsApp (`wa.me`)** — notificación alternativa al aprobador.

## Requisitos previos

- Odoo **19.0** funcionando (Community o Enterprise).
- Python **3.10 o superior**, el requerido por tu instalación de Odoo 19.
- PostgreSQL **13 o superior**.
- `wkhtmltopdf` **0.12.6** si vas a usar la impresión de PDF (Odoo lo requiere
  para los reportes; este módulo intercepta esos reportes).
- Un directorio declarado en `addons_path` donde colocar el módulo.
- Para la notificación completa:
  - Servidor **SMTP** configurado y un correo válido en el aprobador.
  - `web.base.url` apuntando al dominio público de la instancia.
- El usuario aprobador debe tener acceso al módulo **Ventas** para poder abrir
  la orden y ver los botones de aprobación.

## Instalación

1. Clona el repositorio (o copia/enlaza la carpeta) dentro de un directorio de
   tu `addons_path`. El nombre de la carpeta debe ser exactamente
   `sale_credit_approval`:

   ```bash
   # Opción 1: clonar el repositorio
   git clone https://github.com/ssant0/sale_credit_approval.git \
     /opt/odoo/custom-addons/sale_credit_approval

   # Opción 2: copiar el código
   cp -R /ruta/a/sale_credit_approval /opt/odoo/custom-addons/sale_credit_approval

   # Opción 3: enlazar el código fuente para desarrollo
   ln -s /ruta/a/sale_credit_approval /opt/odoo/custom-addons/sale_credit_approval
   ```

2. Agrega el directorio a `addons_path` en tu configuración de Odoo:

   ```ini
   [options]
   addons_path = /opt/odoo/addons,/opt/odoo/custom-addons
   ```

3. Instala el módulo en la base de datos:

   ```bash
   odoo -c /etc/odoo/odoo.conf -d mi_base -i sale_credit_approval --stop-after-init
   ```

   Si no tienes el binario `odoo` en el `PATH`:

   ```bash
   python3 /ruta/a/odoo/odoo-bin -c /etc/odoo/odoo.conf -d mi_base \
     -i sale_credit_approval --stop-after-init
   ```

4. Reinicia el servicio de Odoo:

   ```bash
   sudo systemctl restart odoo
   ```

5. Entra a Odoo y configura el módulo en
   **Contabilidad → Ajustes → Aprobación de crédito en ventas**.

> [!IMPORTANT]
> El nombre técnico es `sale_credit_approval` (carpeta y prefijo de los
> parámetros de configuración). En la lista de Aplicaciones el módulo aparece
> como **Aprobación de Crédito en Ventas**.

## Variables de configuración

Este addon **no usa variables de entorno ni archivo `.env`**. Toda su
configuración son parámetros globales de `ir.config_parameter`, editables desde
**Contabilidad → Ajustes → Aprobación de crédito en ventas**.

| Parámetro | Descripción | Entorno | Requerido |
|---|---|---|---|
| `sale_credit_approval.enabled` | Activa la regla para toda la base de datos | Todos | Sí |
| `sale_credit_approval.cash_term_id` | ID del plazo de pago que se considera contado. Si falta, se usa “Pago inmediato” | Todos | No |
| `sale_credit_approval.user_id` | ID del usuario que puede aprobar o rechazar el crédito | Todos | Sí, para operar la regla |
| `sale_credit_approval.whatsapp` | Número del aprobador con código de país, sin `+` ni espacios (ej. `526681234567`). Si está vacío se usa su teléfono | Todos | No |

> [!IMPORTANT]
> Los parámetros son globales para toda la base de datos, no por compañía.
> Cambiarlos afecta a todas las ventas.

## Uso y desarrollo

### Configuración inicial

1. Ve a **Contabilidad → Ajustes → Aprobación de crédito en ventas**.
2. Activa **Requerir aprobación para ventas a crédito**.
3. Revisa el **Plazo de contado** (por defecto, “Pago inmediato”).
4. Elige el **Aprobador de crédito**. Debe ser un usuario interno con acceso a
   Ventas.
5. Opcionalmente, define el **WhatsApp del aprobador**.

### Flujo de aprobación

1. El vendedor crea una cotización con un plazo de pago distinto al de contado.
2. La orden muestra el aviso **“Venta a crédito: requiere aprobación…”**.
3. El vendedor pulsa **Solicitar aprobación de crédito**. La orden pasa a
   **Pendiente**, se envía un correo al aprobador y se abre un diálogo con el
   botón de WhatsApp.
4. El aprobador abre la orden y pulsa **Aprobar crédito** o **Rechazar
   crédito**.
5. Solo con la aprobación se puede confirmar la orden. Sin ella,
   `action_confirm` se bloquea en el servidor.

### Desarrollo

Para trabajar con recarga automática de Python y XML:

```bash
odoo -c /etc/odoo/odoo.conf -d mi_base -u sale_credit_approval --dev=all
```

Los cambios en modelos, vistas o archivos de datos **no se aplican solos** en
producción: hay que actualizar el módulo.

### Actualización en producción

```bash
# 1. Respalda la base de datos
pg_dump -Fc mi_base > mi_base_$(date +%F).dump

# 2. Actualiza el módulo y detén el servidor al terminar
odoo -c /etc/odoo/odoo.conf -d mi_base -u sale_credit_approval --stop-after-init

# 3. Reinicia el servicio
sudo systemctl restart odoo
```

### Verificación manual

No hay tests automatizados. Para validar un cambio, actualiza el módulo y
recorre esta checklist:

1. Crea una cotización con un plazo de pago a crédito (por ejemplo, 30 días).
2. Debe aparecer el aviso “Venta a crédito: requiere aprobación…”.
3. Pulsa **Solicitar aprobación de crédito**: debe llegar el correo y abrirse
   el diálogo con el botón de WhatsApp.
4. Entra como el aprobador, abre la orden y pulsa **Aprobar crédito**.
5. Confirma la orden: debe permitirlo.
6. Intenta confirmar otra orden a crédito sin aprobar: debe bloquearse.
7. Una cotización con “Pago inmediato” no debe pedir aprobación.
8. Intenta enviar, imprimir y previsualizar una orden pendiente: debe
   bloquearse.

## Comandos disponibles

No hay `Makefile`, `package.json`, `justfile`, tests, CI, lint ni formatter. Los
comandos útiles son los de la CLI de Odoo:

| Comando | Qué hace |
|---|---|
| `odoo -d mi_base -i sale_credit_approval --stop-after-init` | Instala el módulo |
| `odoo -d mi_base -u sale_credit_approval --stop-after-init` | Actualiza el módulo tras cambios en modelos, vistas o datos |
| `odoo -c /etc/odoo/odoo.conf -d mi_base -u sale_credit_approval --dev=all` | Inicia Odoo en modo desarrollo con recarga automática |
| `odoo shell -d mi_base` | Abre una consola interactiva con el entorno de Odoo |

> [!NOTE]
> La verificación real de este addon es manual: instalar o actualizar y recorrer
> la checklist de [Verificación manual](#verificación-manual).

## Cómo funciona

Una cotización es **a crédito** cuando se cumplen estas tres condiciones:

1. La regla está activa (`sale_credit_approval.enabled`).
2. La orden tiene `payment_term_id` definido.
3. El plazo es distinto del plazo de contado configurado.

Sin plazo de pago, la orden **no** se considera a crédito. El módulo no evalúa
montos: el límite de crédito nativo de Odoo (`credit_limit`) sigue siendo un
aviso independiente.

### Puntos de control en el servidor

| Punto de entrada | Método interceptado | Resultado sin aprobación |
|---|---|---|
| Confirmar orden | `sale.order.action_confirm` | `check_credit_approval()` lanza `UserError` |
| Enviar cotización | `sale.order.action_quotation_send` | `_check_credit_gate_actions()` bloquea |
| Previsualizar orden | `sale.order.action_preview_sale_order` | `_check_credit_gate_actions()` bloquea (mantiene `@api.readonly`) |
| Imprimir / PDF | `ir.actions.report._render_qweb_pdf` | Bloquea cualquier reporte de `sale.order` |
| Previsualizar reporte | `ir.actions.report._render_qweb_html` | Bloquea cualquier reporte de `sale.order` |

> [!WARNING]
> Ocultar botones en XML es solo cosmético. Cualquier ruta nueva de envío,
> impresión o previsualización debe llamar a `_check_credit_gate_actions()` o al
> helper correspondiente; de lo contrario se salta el control.

### Cuándo se reinicia la aprobación

La aprobación vuelve a `none` si, después de aprobar, cambia cualquiera de
estas condiciones:

- `sale.order.write` con `payment_term_id` o `partner_id`.
- `sale.order.line.create` (nueva línea).
- `sale.order.line.write` con `product_id`, `product_uom_qty`, `price_unit`,
  `discount` o `tax_id`.
- `sale.order.line.unlink` (eliminar línea).

Si agregas un campo que modifique el importe de la venta, agrégalo también al
filtro de reinicio en `models/sale_order_line.py`.

### Bypass intencional

Las confirmaciones hechas por el **superusuario** (`env.su` /
`SUPERUSER_ID`) se permiten por diseño, para no romper automatizaciones,
importaciones y procesos del sistema. No es un bug.

## Referencia del módulo

### Campos agregados a `sale.order`

| Campo | Tipo | Descripción |
|---|---|---|
| `credit_gate_required` | Boolean (calculado) | `True` si la orden es a crédito y la regla está activa |
| `credit_gate_state` | Selection | `none`, `pending`, `approved` o `rejected` |
| `credit_gate_approved_by` | Many2one `res.users` | Usuario que aprobó el crédito |
| `credit_gate_approved_date` | Datetime | Fecha y hora de la aprobación |
| `credit_gate_is_approver` | Boolean (calculado) | `True` si el usuario actual es el aprobador configurado |
| `credit_gate_message` | Char (calculado) | Aviso de estado mostrado en la orden |

### Acciones

| Método | Uso |
|---|---|
| `action_request_credit_approval()` | Pasa la orden a `pending`, envía el correo y abre el diálogo de notificación |
| `action_approve_credit()` | Aprueba el crédito; solo el aprobador y solo en estado `pending` |
| `action_reject_credit()` | Rechaza el crédito; solo el aprobador y solo en estado `pending` |
| `action_open_whatsapp()` | Abre el enlace `wa.me` desde el diálogo de notificación |

### Modelo transitorio

`sale.credit.approval.notify` es el diálogo que aparece al solicitar la
aprobación. Muestra el resumen de la orden, si el correo se envió y el botón de
WhatsApp cuando hay un número disponible.

### Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `models/credit_gate.py` | Toda la lógica del control: definición de crédito, aprobador, correo y WhatsApp |
| `models/sale_order.py` | Campos, acciones y puntos de control de la orden |
| `models/sale_order_line.py` | Reinicio de la aprobación por cambios en líneas |
| `models/ir_actions_report.py` | Bloqueo de impresión y previsualización de reportes |
| `models/res_config_settings.py` | Campos de configuración global |
| `models/sale_credit_approval_notify.py` | Diálogo de notificación al aprobador |
| `views/*.xml` | Botones, avisos y pantalla de ajustes |
| `security/ir.model.access.csv` | Acceso al modelo transitorio de notificación |

## Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| No pide aprobación | La regla está apagada, el plazo es el de contado o no se guardó la configuración |
| No aparece el botón “Aprobar crédito” | El usuario actual no es el aprobador configurado |
| El aprobador no puede abrir la orden | No tiene acceso al módulo Ventas |
| El correo no llega | SMTP sin configurar o el aprobador no tiene correo |
| El enlace abre `localhost` | `web.base.url` no apunta al dominio público |
| La aprobación desapareció | Se cambió el plazo, el cliente o una línea; hay que solicitar de nuevo |
| No se puede imprimir ni previsualizar | Es el comportamiento esperado hasta que la orden esté aprobada |

## Limitaciones

- La regla se basa en el **plazo de pago**, no en el monto. El límite de crédito
  nativo de Odoo sigue siendo solo un aviso y es independiente.
- No cubre confirmaciones automáticas hechas por el sistema (superusuario).
- Hay un **único aprobador global**; no se configura por compañía, equipo ni
  vendedor.
- Si el aprobador es el mismo vendedor, puede aprobar su propia venta. Es una
  decisión de configuración, no un bug.
- No hay tests automatizados, CI, lint ni formatter; la verificación es manual.

## Contribuir

1. Crea una rama desde la principal con un nombre descriptivo:
   - `feat/<descripcion-corta>` para funcionalidad nueva.
   - `fix/<descripcion-corta>` para correcciones.
   - `docs/<descripcion-corta>` para documentación.
2. Sigue **Conventional Commits**:

   ```text
   feat: bloquear previsualización sin aprobación
   fix: reiniciar aprobación al cambiar impuestos de una línea
   docs: documentar parámetros de configuración
   ```

3. Mantén el cambio enfocado. Si tocas modelos, vistas o datos, actualiza el
   módulo y recorre la checklist de verificación manual.
4. Si cambia el comportamiento o la arquitectura, actualiza `README.md` y
   `AGENTS.md` en el mismo cambio.
5. Abre el PR explicando **qué** cambia, **por qué** y **cómo lo probaste**.

Convenciones del proyecto:

- Los textos visibles para el usuario van en **español**.
- Las vistas usan la sintaxis de Odoo 19: `invisible="..."` y
  `readonly="..."`, nunca `attrs`.
- La lógica del control vive en `models/credit_gate.py`; los demás modelos solo
  la conectan.

## Licencia

Este módulo es software libre y gratuito. Se distribuye bajo la **GNU Lesser
General Public License v3.0 (LGPL-3.0)**, cuyo texto está en
[`LICENSE`](LICENSE); los términos de la GNU GPL v3.0 que complementan la LGPL
están en [`COPYING`](COPYING). La declaración del addon está en
`__manifest__.py`.

Copyright (C) 2026 ssant0. Puedes usarlo, modificarlo y redistribuirlo bajo los
términos de esa licencia.

Autor: [ssant0](https://github.com/ssant0).
