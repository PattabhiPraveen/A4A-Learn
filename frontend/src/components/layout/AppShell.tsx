import { Outlet } from "react-router-dom";

import Footer from "./Footer";
import Header from "./Header";
import MobileNavigation from "./MobileNavigation";

export default function AppShell() {
  return (
    <>
      <a
        href="#main-content"
        className="skip-link"
      >
        Skip to main content
      </a>

      <Header />

      <main
        id="main-content"
        className="main-content"
        tabIndex={-1}
      >
        <Outlet />
      </main>

      <Footer />

      <MobileNavigation />
    </>
  );
}
