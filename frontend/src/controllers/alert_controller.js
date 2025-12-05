import { Controller } from "@hotwired/stimulus"

/**
 * Alert Controller - Dismissable notifications
 * 
 * Usage in Jinja2:
 * {% from "components/macros.html" import alert %}
 * {{ alert("Success!", type="success", dismissable=true) }}
 * 
 * Optional auto-dismiss with data-alert-auto-dismiss-value="3000" (ms)
 */
export default class extends Controller {
    static values = {
        autoDismiss: { type: Number, default: 0 }  // 0 = no auto dismiss
    }

    connect() {
        if (this.autoDismissValue > 0) {
            this.timeout = setTimeout(() => this.dismiss(), this.autoDismissValue)
        }
    }

    disconnect() {
        if (this.timeout) {
            clearTimeout(this.timeout)
        }
    }

    dismiss() {
        // Add fade-out animation
        this.element.style.opacity = "0"
        this.element.style.transform = "translateX(100%)"
        this.element.style.transition = "all 0.3s ease-out"

        setTimeout(() => {
            this.element.remove()
        }, 300)
    }
}
