import { BrowserRouter, Link, Route, Routes } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Visualizer from "./pages/Visualizer";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<VisualizerWithNav />} />
        <Route path="/dashboard" element={<DashboardWithNav />} />
      </Routes>
    </BrowserRouter>
  );
}

function VisualizerWithNav() {
  return (
    <>
      <nav className="border-b border-gray-200 bg-white">
        <div className="px-8 py-3">
          <Link
            to="/dashboard"
            className="text-sm font-medium text-brand-600 hover:text-brand-700 hover:underline"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </nav>
      <Visualizer />
    </>
  );
}

function DashboardWithNav() {
  return (
    <>
      <nav className="border-b border-gray-200 bg-white">
        <div className="px-8 py-3">
          <div className="flex items-center gap-2">
            <img src="/logo.svg" alt="Magentic Logo" className="h-6 w-6" />
            <h1
              className="bg-clip-text text-lg font-bold text-transparent"
              style={{ backgroundImage: "linear-gradient(120deg, #fb81ff, #922185 30%)" }}
            >
              Magentic Marketplace
            </h1>
          </div>
        </div>
      </nav>
      <Dashboard />
    </>
  );
}

export default App;
