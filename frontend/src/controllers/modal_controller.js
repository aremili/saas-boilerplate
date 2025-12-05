import { Controller } from "@hotwired/stimulus"

/**
 * Modal Controller
 * 
 * Usage in Jinja2:
 * {% include "components/modal.html" %}
 * 
 * Data attributes:
 * - data-controller="modal"
 * - data-modal-target="dialog" on the modal backdrop/container
 * - data-action="click->modal#open" on trigger buttons
 * - data-action="click->modal#close" on close buttons
 */
export default class extends Controller {
    static targets = ["dialog"]

    connect() {
        // Handle escape key
        this.handleKeydown = this.handleKeydown.bind(this)
        document.addEventListener("keydown", this.handleKeydown)
    }

    disconnect() {
        document.removeEventListener("keydown", this.handleKeydown)
    }

    open() {
        this.dialogTarget.classList.remove("hidden")
        document.body.style.overflow = "hidden"
    }

    close() {
        this.dialogTarget.classList.add("hidden")
        document.body.style.overflow = ""
    }

    closeOnBackdrop(event) {
        // Only close if clicking the backdrop itself, not its children
        if (event.target === this.dialogTarget) {
            this.close()
        }
    }

    handleKeydown(event) {
        if (event.key === "Escape" && !this.dialogTarget.classList.contains("hidden")) {
            this.close()
        }
    }
}
