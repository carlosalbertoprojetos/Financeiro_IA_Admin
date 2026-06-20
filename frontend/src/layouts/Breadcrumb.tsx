"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { buildBreadcrumbs } from "@/shared/navigation/breadcrumbs";

export function Breadcrumb() {
  const pathname = usePathname();
  const items = buildBreadcrumbs(pathname);

  return (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-sm">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        return (
          <span key={`${item.label}-${index}`} className="flex items-center gap-1">
            {index > 0 ? <span className="text-muted">/</span> : null}
            {item.href && !isLast ? (
              <Link href={item.href} className="text-muted-foreground hover:text-foreground">
                {item.label}
              </Link>
            ) : (
              <span className={isLast ? "font-medium text-foreground" : "text-muted-foreground"}>
                {item.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
