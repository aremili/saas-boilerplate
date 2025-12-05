import { Controller } from "@hotwired/stimulus"

/**
 * Dropdown Controller
 * 
 * Usage in Jinja2:
 * {% include "components/dropdown.html" %}
 * 
 * Data attributes:
 * - data-controller="dropdown"
 * - data-dropdown-target="menu" on the dropdown content
 * - data-action="click->dropdown#toggle" on the trigger button
 */
export default class extends Controller {
    static targets = ["menu"]

    connect() {
        // Close dropdown when clicking outside
        this.handleClickOutside = this.handleClickOutside.bind(this)
        document.addEventListener("click", this.handleClickOutside)
    }

    disconnect() {
        document.removeEventListener("click", this.handleClickOutside)
    }

    toggle(event) {
        event.stopPropagation()
        this.menuTarget.classList.toggle("hidden")
    }

    hide() {
        this.menuTarget.classList.add("hidden")
    }

    handleClickOutside(event) {
        if (!this.element.contains(event.target)) {
            this.hide()
        }
    }
}
