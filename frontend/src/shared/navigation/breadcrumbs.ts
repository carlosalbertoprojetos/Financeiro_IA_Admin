import { TIP_APP_PAGES } from "@/page-views/registry";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function buildBreadcrumbs(pathname: string | null): BreadcrumbItem[] {
  const crumbs: BreadcrumbItem[] = [{ label: "TIP", href: "/dashboard" }];

  if (!pathname || pathname === "/dashboard") {
    crumbs.push({ label: "Dashboard" });
    return crumbs;
  }

  const page = TIP_APP_PAGES.find(
    (item) => pathname === item.path || pathname.startsWith(`${item.path}/`),
  );

  if (page) {
    crumbs.push({ label: page.label });
  } else {
    crumbs.push({ label: "Página" });
  }

  return crumbs;
}
