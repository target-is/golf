from odoo import models, fields
from markupsafe import Markup, escape


class RepairOrder(models.Model):
    _inherit = "repair.order"

    confirmed_by_id = fields.Many2one(
        "res.users",
        string="Confirmed By",
        readonly=True,
        copy=False
    )

    def action_open_cancel_wizard(self):
        self.ensure_one()
        return {
            "name": "Cancel Repair Order",
            "type": "ir.actions.act_window",
            "res_model": "repair.cancel.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_repair_id": self.id
            }
        }

    def action_validate(self):
        res = super().action_validate()
        for rec in self:
            if not rec.confirmed_by_id:
                rec.confirmed_by_id = self.env.user
        return res


class RepairCancelWizard(models.TransientModel):
    _name = "repair.cancel.wizard"
    _description = "Cancel Repair Wizard"

    repair_id = fields.Many2one(
        "repair.order",
        required=True,
        readonly=True
    )

    reason = fields.Text(
        string="Cancellation Reason",
        required=True
    )

    def action_confirm_cancel(self):
        self.ensure_one()
        repair = self.repair_id
        user = self.env.user

        # =========================
        # 1) Cancel Repair
        # =========================
        repair.action_repair_cancel()

        # =========================
        # 2) Log Note (HTML)
        # =========================
        body = Markup(f"""
            <div>
                <b style="color:#d9534f;">❌ Repair Order Cancelled</b><br/><br/>
                <b>Cancelled By:</b> {escape(user.name)}<br/><br/>
                <b>Reason:</b>
                <div style="
                    margin-top:6px;
                    padding:10px;
                    border-left:4px solid #d9534f;
                    background:#f9f9f9;
                    border-radius:4px;
                ">
                    {escape(self.reason)}
                </div>
            </div>
        """)

        repair.message_post(
            body=body,
            subtype_xmlid="mail.mt_note"
        )

        # =========================
        # 3) Create Activity for CONFIRMER
        # =========================
        last_confirmer = repair.confirmed_by_id
        if last_confirmer:
            model_id = self.env["ir.model"]._get_id("repair.order")
            activity_type = self.env.ref("mail.mail_activity_data_todo")

            self.env["mail.activity"].sudo().create({
                "res_model_id": model_id,
                "res_id": repair.id,
                "activity_type_id": activity_type.id,
                "user_id": last_confirmer.id,
                "summary": "Repair Order Cancelled",
                "note": f"""
            <b>Repair Order has been cancelled</b><br/><br/>
            <b>Reason:</b><br/>
            {self.reason}
            """,
            })

            # 3) ✅ Success Toast Notification
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Repair Order Cancelled",
                "message": f"Repair Order {repair.name} has been cancelled successfully.",
                "type": "info",
                "sticky": False,

                # 👇 👇 👇 ده المهم
                "next": {
                    "type": "ir.actions.act_window_close"
                }
            }
        }


