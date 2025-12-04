import './styles/index.css';
import 'htmx.org';
import { Application } from '@hotwired/stimulus';
import HelloController from "./controllers/hello_controller";

// Initialize Stimulus
window.Stimulus = Application.start();
window.Stimulus.register("hello", HelloController);

console.log('Frontend initialized');
