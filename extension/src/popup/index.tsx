// Polyfill process to prevent ReferenceError from dependencies expecting Node.js
// eslint-disable-next-line @typescript-eslint/no-explicit-any
if (typeof (globalThis as any).process === "undefined") {
  (globalThis as any).process = {
    env: { NODE_ENV: "production" },
    nextTick: (fn: () => void) => setTimeout(fn, 0),
  };
}

import React from "react";
import ReactDOM from "react-dom/client";
import "../index.css";
import { Login } from "./Login";

function mount() {
  const container = document.getElementById("root");
  if (!container) {
    console.error("[Fiscal Guard] Root element not found");
    return;
  }
  ReactDOM.createRoot(container).render(
    <React.StrictMode>
      <Login />
    </React.StrictMode>,
  );
}

// Ensure DOM is ready before mounting
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mount);
} else {
  mount();
}
