/* @odoo-module */

// Importing necessary components from Odoo's web module.
// ActionMenus is a component that manages the action menus in the Odoo interface.
// patch is used to modify or extend existing functionality in a safe way.
import { ActionMenus } from "@web/search/action_menus/action_menus";
import { patch } from "@web/core/utils/patch";

// Using the `patch` function to modify the prototype of the ActionMenus class.
// This allows us to extend or change the behavior of the `getActionItems` method in ActionMenus.
patch(ActionMenus.prototype, {
  // Overriding the `getActionItems` method to customize its behavior.
  async getActionItems(props) {
    // Calling the original `getActionItems` method using `super` and waiting for the result.
    var res = await super.getActionItems(props);
//    console.log("This log message from the action_menus.js , i would like to know what is the value of the RES" , res)
    // Checking if there are any items in the response.
    if(res.length > 0) {

      // Calling a method from the 'access.management' model to get some removal options.
      // It seems to be checking for restrictions on certain actions based on the provided model (`this.props.resModel`).
      const RestActions = await this.orm.call(
        "access.management",   // Model name: 'access.management'
        "get_remove_options",  // Method name to get the options to be removed
        [1, this.props.resModel] // Arguments passed to the method (1 and the model name)
      );

      // Calling another method to check whether export actions should be hidden.
      const isExportHidden = await this.orm.call(
        "access.management",   // Model name: 'access.management'
        "is_export_hide",      // Method name to check if export action should be hidden
        [1, this.props.resModel] // Arguments passed to the method (1 and the model name)
      );

      // If export is hidden, filter the result to exclude actions that should be removed (based on RestActions).
      // Also remove the 'export' action if it is present.
      if (isExportHidden) {
        return res.filter(
          (ele) =>
            // Exclude actions based on RestActions and remove the 'export' action.
            !RestActions.includes(ele.key) && ele.key != "export"
        );
      }

      // If export is not hidden, just filter out the actions in RestActions.
      return res.filter((ele) => !RestActions.includes(ele.key));
    }

    // If there are no items, simply return the result as it is.
    return res;
  },
});
