/**
 * 应用入口:
 * - 装 BrowserRouter / QueryClientProvider
 * - 启动时应用 tone / appearance 到 <html>(主题层就位)
 * - 引入主题变量 + reset
 */
import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";

import App from "./App";
import { queryClient } from "./lib/queryClient";
import { applyHtmlAttrs } from "./store/theme";

import "./styles/themes.css";
import "./styles/reset.css";

// 启动时立刻把 tone / appearance 写到 <html>(避免首屏闪烁)
applyHtmlAttrs();

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
