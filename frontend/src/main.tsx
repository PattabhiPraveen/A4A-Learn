import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./app/App";

import {
  AuthProvider,
} from "./contexts/AuthContext";

import "./styles/global.css";
import "./styles/app.css";

const rootElement =
  document.getElementById("root");

if (!rootElement) {
  throw new Error(
    "Root element '#root' was not found.",
  );
}

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);