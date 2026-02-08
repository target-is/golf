/* @odoo-module */

import { FormRenderer } from "@web/views/form/form_renderer";
import { ListController } from "@web/views/list/list_controller";
import { FormController } from "@web/views/form/form_controller";
import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
//import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { cookie } from "@web/core/browser/cookie";
import { user } from "@web/core/user";

import { onMounted } from "@odoo/owl";

patch(FormRenderer.prototype, {
  setup() {
    super.setup();
    this.orm = useService("orm");
    const self = this;
    const handleElementRemoval = (selector) => {
        const interval = setInterval(() => {
            const element = document.querySelector(selector);
            if (element) {
                element.remove();
                clearInterval(interval);
            }
        }, 50); // Check every 50ms
    };
    const configureChatterVisibility = async () => {
        let cids_str = cookie.get("cids");
        let cids = cids_str.split('-').map(Number);
        let model = this.env.model.config.resModel;
        let user_id = user.userId
        if (cids && model) {
        try {
        const result = self.orm
        .call("access.management", "get_chatter_hide_details", [user_id, cids, model])
        .then(function (result) {
            console.log("test to see the result of result['hide_send_mail']", result['hide_send_mail'])
            if (!result['hide_send_mail']) {
                handleElementRemoval(".o-mail-Chatter-sendMessage");
            }
            if (!result['hide_log_notes']) {
                handleElementRemoval(".o-mail-Chatter-logNote");
            }
            if (!result['hide_schedule_activity']) {
                handleElementRemoval(".o-mail-Chatter-activity");
            }
        })
        }catch (error) {
            console.error("Error fetching chatter visibility config:", error);
        }
        }
    }
    configureChatterVisibility();
  },
});
