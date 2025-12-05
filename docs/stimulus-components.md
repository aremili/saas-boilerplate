# Stimulus + Jinja2 Component System

This guide explains how to build reusable UI components by combining **Stimulus controllers** (JavaScript) with **Jinja2 templates** (HTML).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Jinja2 Template                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  <div data-controller="counter"                       │  │
│  │       data-counter-count-value="{{ initial }}">       │  │ ← Data flows IN
│  │       ...                                             │  │
│  │  </div>                                               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Stimulus Controller                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  static values = { count: Number }                    │  │
│  │  countValueChanged() { this.render() }                │  │ ← JS handles behavior
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key principle**: HTML owns structure & data, JavaScript owns behavior.

---

## File Organization

```
frontend/src/controllers/
├── dropdown_controller.js     # Each controller = one behavior
├── modal_controller.js
├── counter_controller.js
└── alert_controller.js

app/templates/components/
├── dropdown.html              # Matching template component
├── modal.html
├── counter.html
└── macros.html                # Small components as macros
```

**Naming convention**: `{name}_controller.js` ↔ `data-controller="{name}"`

---

## Core Concepts

### 1. Connecting Controllers to Elements

Add `data-controller` to any element to activate a controller:

```html
<div data-controller="dropdown">
  <!-- Controller is now active on this element -->
</div>
```

The controller's `connect()` method runs when the element enters the DOM.

### 2. Targets (Controller → Element References)

Define targets to reference child elements from your controller:

```html
<div data-controller="dropdown">
  <div data-dropdown-target="menu">...</div>
</div>
```

```javascript
export default class extends Controller {
  static targets = ["menu"]
  
  toggle() {
    this.menuTarget.classList.toggle("hidden")  // Access via this.{name}Target
  }
}
```

### 3. Actions (Element → Controller Methods)

Bind events to controller methods with `data-action`:

```html
<button data-action="click->dropdown#toggle">
  Open Menu
</button>
```

Format: `{event}->{controller}#{method}`

Common events: `click`, `submit`, `input`, `change`, `keydown`

### 4. Values (Jinja2 → Controller Data)

Pass data from Jinja2 to JavaScript via value attributes:

```html
<!-- Jinja2 template -->
<div data-controller="counter"
     data-counter-count-value="{{ initial_count }}"
     data-counter-step-value="{{ step }}">
```

```javascript
export default class extends Controller {
  static values = {
    count: { type: Number, default: 0 },
    step: { type: Number, default: 1 }
  }
  
  increment() {
    this.countValue += this.stepValue  // Access via this.{name}Value
  }
  
  countValueChanged() {
    // Called automatically when value changes
  }
}
```

---

## Component Patterns

### Pattern A: Include with Variables

Best for: Components with configurable content.

**Template** (`components/dropdown.html`):
```html
<div data-controller="dropdown" class="relative">
  <button data-action="click->dropdown#toggle">
    {{ label }}
  </button>
  <div data-dropdown-target="menu" class="hidden">
    {% for item in items %}
      <a href="{{ item.href }}">{{ item.text }}</a>
    {% endfor %}
  </div>
</div>
```

**Usage**:
```html
{% with label="Actions", items=[{"text": "Edit", "href": "#"}] %}
  {% include "components/dropdown.html" %}
{% endwith %}
```

### Pattern B: Include with Blocks

Best for: Components where you need to customize internal structure.

**Template** (`components/modal.html`):
```html
<div data-controller="modal">
  <button data-action="click->modal#open">
    {% block modal_trigger %}Open{% endblock %}
  </button>
  <div data-modal-target="dialog" class="hidden">
    {% block modal_content %}Default content{% endblock %}
  </div>
</div>
```

**Usage** (extend to override blocks):
```html
{% extends "components/modal.html" %}
{% block modal_content %}
  <p>Custom modal content here!</p>
{% endblock %}
```

### Pattern C: Macros

Best for: Small, frequently-used components with many variations.

**Template** (`components/macros.html`):
```html
{% macro alert(message, type="info", dismissable=true) %}
<div data-controller="alert" class="alert alert-{{ type }}">
  {{ message }}
  {% if dismissable %}
    <button data-action="click->alert#dismiss">×</button>
  {% endif %}
</div>
{% endmacro %}
```

**Usage**:
```html
{% from "components/macros.html" import alert %}
{{ alert("Success!", type="success") }}
{{ alert("Warning!", type="warning", dismissable=false) }}
```

---

## Registering Controllers

All controllers must be registered in `frontend/src/main.js`:

```javascript
import { Application } from '@hotwired/stimulus';
import DropdownController from "./controllers/dropdown_controller";

window.Stimulus = Application.start();
window.Stimulus.register("dropdown", DropdownController);
```

---

## Creating a New Component

### Step 1: Create the Controller

```javascript
// frontend/src/controllers/accordion_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["content"]
  static values = { open: Boolean }
  
  toggle() {
    this.openValue = !this.openValue
  }
  
  openValueChanged() {
    this.contentTarget.classList.toggle("hidden", !this.openValue)
  }
}
```

### Step 2: Create the Template

```html
<!-- app/templates/components/accordion.html -->
<div data-controller="accordion" 
     data-accordion-open-value="{{ open | default(false) | tojson }}">
  <button data-action="click->accordion#toggle">
    {{ title }}
  </button>
  <div data-accordion-target="content" class="{% if not open %}hidden{% endif %}">
    {% block content %}{{ content }}{% endblock %}
  </div>
</div>
```

### Step 3: Register the Controller

```javascript
// frontend/src/main.js
import AccordionController from "./controllers/accordion_controller";
window.Stimulus.register("accordion", AccordionController);
```

### Step 4: Use It

```html
{% with title="FAQ", content="Answer here...", open=true %}
  {% include "components/accordion.html" %}
{% endwith %}
```

---

## Tips & Best Practices

| Do | Don't |
|----|-------|
| Pass data via `data-*-value` attributes | Embed JavaScript in templates |
| Keep controllers focused on one behavior | Create monolithic controllers |
| Use `connect()`/`disconnect()` for setup/cleanup | Forget to remove event listeners |
| Match controller names to file names | Use inconsistent naming |

---

## Available Components

| Component | Controller | Template | Pattern |
|-----------|------------|----------|---------|
| Dropdown | `dropdown` | `dropdown.html` | Include |
| Modal | `modal` | `modal.html` | Include + Blocks |
| Counter | `counter` | `counter.html` | Include + Values |
| Alert | `alert` | `macros.html` | Macro |
| Badge | — | `macros.html` | Macro (no JS) |
| Button | — | `macros.html` | Macro (no JS) |

---

## Further Reading

- [Stimulus Handbook](https://stimulus.hotwired.dev/handbook/introduction)
- [Jinja2 Template Designer](https://jinja.palletsprojects.com/en/3.1.x/templates/)
