import { Controller } from "@hotwired/stimulus"

/**
 * Checkbox Controller - Styled checkbox with form integration
 * 
 * Usage in Jinja2:
 * {% include "components/checkbox.html" %}
 * 
 * Features:
 * - Custom styled checkbox
 * - Syncs with hidden input for form submission
 * - Optional callback on change
 */
export default class extends Controller {
    static targets = ["input", "box"]
    static values = {
        checked: { type: Boolean, default: false }
    }

    connect() {
        this.render()
    }

    toggle() {
        this.checkedValue = !this.checkedValue
    }

    checkedValueChanged() {
        this.render()

        // Update hidden input if it exists
        if (this.hasInputTarget) {
            this.inputTarget.value = this.checkedValue ? "true" : "false"
            this.inputTarget.checked = this.checkedValue
        }

        // Dispatch custom event for other components to listen
        this.element.dispatchEvent(new CustomEvent('checkbox:changed', {
            bubbles: true,
            detail: { checked: this.checkedValue }
        }))
    }

    render() {
        if (this.hasBoxTarget) {
            if (this.checkedValue) {
                this.boxTarget.classList.add('bg-blue-600', 'border-blue-600')
                this.boxTarget.classList.remove('border-gray-300', 'bg-white')
                this.boxTarget.innerHTML = `
                    <svg class="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                    </svg>
                `
            } else {
                this.boxTarget.classList.remove('bg-blue-600', 'border-blue-600')
                this.boxTarget.classList.add('border-gray-300', 'bg-white')
                this.boxTarget.innerHTML = ''
            }
        }
    }
}
