// Must import before ./App: chart components read resolved CSS custom
// properties (chartTheme.ts) at module-evaluation time, so the stylesheet
// that defines them has to already be in the document by then — ESM
// evaluates sibling imports in source order.
import "./theme/tokens.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import { App } from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
