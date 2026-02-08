/** @odoo-module **/
// This annotation is specific to Odoo's module system. It indicates that this file is a JavaScript module for Odoo.
// Odoo modules help in encapsulating functionality and ensuring compatibility with the framework.

import { Component, useState } from "@odoo/owl";
// Importing the necessary elements from OWL (Odoo Web Library):
// - `Component`: Base class for creating components in OWL.
// - `useState`: A function to manage reactive state within components (though not used in this code snippet).

// Define a new component named `DateSelectionBits`.
export class DateSelectionBits extends Component {
    // The `setup` method initializes the component. This is called when the component is created.
    setup() {
        // Check if `this.props.value` can be converted to a valid date.
        // `this.props` refers to the properties passed to the component, which are inputs from the parent component.
        if (!isNaN(new Date(this.props.value))) {
            // If `this.props.value` is a valid date, update the value to "today".
            // `this.props.update` is a callback function passed from the parent to update the state.
            this.props.update("today");
            // Update `this.props.value` locally to "today".
            this.props.value = "today";
        }
    }

    // The `onchange` method is triggered when the value in the associated DOM element changes.
    onchange(ev) {
        // `ev.target.value` is the new value entered by the user or selected in the UI.
        // Call the parent-provided `update` method with this new value to synchronize the state.
        this.props.update(ev.target.value);
    }
}

// Define the template associated with the component.
// This links the component's logic to a template defined in Odoo's QWeb system.
// The template `advanced_web_domain_widget.DateSelectionBits` should be defined elsewhere in XML.
DateSelectionBits.template = "advanced_web_domain_widget.DateSelectionBits";
