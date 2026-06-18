/**
 * SIP-Edge Frontend — Entry point.
 * Mounts the Svelte App component using Svelte 5 mount() API.
 */
import { mount } from "svelte";
import App from "./App.svelte";
import "./app.css";

const app = mount(App, {
  target: document.getElementById("app"),
});

export default app;
