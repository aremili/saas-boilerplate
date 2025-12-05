import './styles/index.css';
import 'htmx.org';
import { Application } from '@hotwired/stimulus';

// Import all controllers
import HelloController from "./controllers/hello_controller";
import DropdownController from "./controllers/dropdown_controller";
import ModalController from "./controllers/modal_controller";
import CounterController from "./controllers/counter_controller";
import AlertController from "./controllers/alert_controller";
import CheckboxController from "./controllers/checkbox_controller";

// Initialize Stimulus
window.Stimulus = Application.start();

// Register all controllers
window.Stimulus.register("hello", HelloController);
window.Stimulus.register("dropdown", DropdownController);
window.Stimulus.register("modal", ModalController);
window.Stimulus.register("counter", CounterController);
window.Stimulus.register("alert", AlertController);
window.Stimulus.register("checkbox", CheckboxController);

console.log('Frontend initialized');
