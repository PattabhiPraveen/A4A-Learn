import { NavLink } from "react-router-dom";

const mobileItems = [
  { to: "/", label: "Home" },
  { to: "/learn", label: "Learn" },
  { to: "/tutor", label: "Tutor" },
  { to: "/isl", label: "ISL" },
  { to: "/progress", label: "Progress" },
];

export default function MobileNavigation() {
  return (
    <nav
      className="mobile-navigation"
      aria-label="Mobile navigation"
    >
      {mobileItems.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.to === "/"}
          className={({ isActive }) =>
            isActive
              ? "mobile-nav-link mobile-nav-link--active"
              : "mobile-nav-link"
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
