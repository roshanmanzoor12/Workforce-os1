"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BriefcaseBusiness, Building2, ChevronDown, MessageSquareMore, MonitorUp, Settings, Users, Wallet } from "lucide-react";
import type { WorkspaceNavigationGroup, WorkspaceNavigationItem } from "@/lib/workspace/navigation";
import type { WorkspaceType } from "@/types/workspace";
import { getWorkspaceTemplate } from "@/lib/workspace/templates";

export function WorkspaceNavigation({ items, pathname, search, workspaceId, type }: {
  items: WorkspaceNavigationItem[]; pathname: string; search: string; workspaceId: string | null; type?: WorkspaceType;
}) {
  const words = getWorkspaceTemplate(type);
  const [expanded, setExpanded] = useState<string[]>(["organization"]);
  useEffect(() => { setExpanded(["organization"]); }, [workspaceId]);
  const query = search.trim().toLowerCase();
  const definitions = [
    { key: "organization", label: words.organization, icon: Building2 },
    { key: "people", label: words.people, icon: Users },
    { key: "communication", label: "Communication", icon: MessageSquareMore },
    { key: "work", label: words.work, icon: BriefcaseBusiness },
    { key: "finance", label: words.finance, icon: Wallet },
    { key: "monitoring", label: words.monitoring, icon: MonitorUp },
    { key: "administration", label: "Administration", icon: Settings },
  ] as const;
  const active = (href: string) => pathname === href || (href !== "/dashboard" && href !== "/settings" && pathname.startsWith(href + "/"));
  useEffect(() => {
    const selected = items.find(item => active(item.href))?.group;
    if (selected) setExpanded(current => current.includes(selected) ? current : [...current, selected]);
  }, [pathname, workspaceId, items]);
  function row(item: WorkspaceNavigationItem) {
    const Icon = item.icon;
    return <li key={item.key}><Link className="wo-sidebarLink" href={item.href} aria-current={active(item.href) ? "page" : undefined}>
      <Icon aria-hidden="true" size={18} strokeWidth={1.7} /><span>{item.label}</span>
    </Link></li>;
  }
  function group(key: WorkspaceNavigationGroup) {
    const definition = definitions.find(item => item.key === key)!;
    const children = items.filter(item => item.group === key && (!query || item.label.toLowerCase().includes(query) || definition.label.toLowerCase().includes(query)));
    if (!children.length) return null;
    const open = Boolean(query) || expanded.includes(key);
    const Icon = definition.icon;
    const id = `workspace-menu-${workspaceId ?? "none"}-${key}`;
    return <section key={key} className="wo-navGroup">
      <button type="button" className="wo-navGroupButton" aria-expanded={open} aria-controls={id}
        onClick={() => setExpanded(current => current.includes(key) ? current.filter(item => item !== key) : [...current, key])}>
        <Icon size={18} strokeWidth={1.7} aria-hidden="true" /><span>{definition.label}</span><ChevronDown size={15} aria-hidden="true" style={{ transform: open ? "rotate(180deg)" : undefined }} />
      </button>
      <ul id={id} hidden={!open} className="wo-navChildren">{children.map(row)}</ul>
    </section>;
  }
  const standalone = (key: string) => {
    const item = items.find(entry => entry.key === key && (!query || entry.label.toLowerCase().includes(query)));
    return item ? <ul key={key}>{row(item)}</ul> : null;
  };
  const anyMatch = items.some(item => item.label.toLowerCase().includes(query) || definitions.some(definition => definition.key === item.group && definition.label.toLowerCase().includes(query)));
  return <div className="wo-workspaceMenu">
    {standalone("dashboard")}
    {definitions.filter(item => item.key !== "administration").map(item => group(item.key))}
    {standalone("workspace-ai")}{standalone("reports")}{group("administration")}
    {!anyMatch && <p className="wo-sidebarEmpty" role="status">No menu items match your search.</p>}
    <style jsx>{`
      .wo-workspaceMenu { padding-bottom: 12px; }
      .wo-workspaceMenu ul { padding: 0; margin: 0; list-style: none; }
      .wo-navGroup { margin-block: 4px; }
      .wo-navGroupButton { width: 100%; display: flex; align-items: center; gap: 12px; min-height: 42px; padding: 10px 14px; border: 0; background: transparent; color: var(--color-text-primary, #1e2833); font: inherit; font-size: 13px; text-align: start; cursor: pointer; border-radius: 8px; }
      .wo-navGroupButton span { flex: 1; }
      .wo-navGroupButton:focus-visible { outline: 2px solid #b87b00; outline-offset: -2px; }
      .wo-navChildren { padding-inline-start: 22px !important; }
      .wo-navChildren[hidden] { display: none; }
    `}</style>
  </div>;
}
