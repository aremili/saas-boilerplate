import { Controller } from "@hotwired/stimulus"

/**
 * Counter Controller - Demonstrates Stimulus Values
 * 
 * Usage in Jinja2:
 * <div data-controller="counter" 
 *      data-counter-count-value="{{ initial_count }}"
 *      data-counter-step-value="{{ step }}">
 * 
 * Values can be passed dynamically from Jinja2 context!
 * 
 * To sync with a hidden input for form submission:
 * <input type="hidden" data-counter-target="input" name="field_name">
 */
export default class extends Controller {
    static targets = ["display", "input"]
    static values = {
        count: { type: Number, default: 0 },
        step: { type: Number, default: 1 },
        min: { type: Number, default: -Infinity },
        max: { type: Number, default: Infinity }
    }

    connect() {
        this.render()
    }

    increment() {
        if (this.countValue + this.stepValue <= this.maxValue) {
            this.countValue += this.stepValue
        }
    }

    decrement() {
        if (this.countValue - this.stepValue >= this.minValue) {
            this.countValue -= this.stepValue
        }
    }

    reset() {
        this.countValue = 0
    }

    // Called automatically when countValue changes
    countValueChanged() {
        this.render()
    }

    render() {
        if (this.hasDisplayTarget) {
            this.displayTarget.textContent = this.countValue
        }
        // Sync with hidden input for form submission
        if (this.hasInputTarget) {
            this.inputTarget.value = this.countValue
        }
    }
}
