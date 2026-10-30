#!/usr/bin/env python3
"""Safe current-source frontend Live Screen employee-list repair.
Usage: python WorkforceOS-LiveScreen-Employee-List-Fix.py [--apply]
No authentication/authorization logic is bypassed.
"""
from __future__ import annotations
import argparse
import ast
import datetime
import pathlib
import shutil
import sys

ROOT = pathlib.Path(r'C:\workforce-os') if sys.platform == 'win32' else pathlib.Path('/tmp/workforce-os')
REL = pathlib.Path('apps/web/app/(workspace)/monitoring/live-screen/page.tsx')

OLD_IMPORT = '''import {
  monitoringService,
  type MonitoringSnapshot,
} from "@/services/monitoring.service";'''
NEW_IMPORT = OLD_IMPORT

OLD_RESULTS = '''      const results = await Promise.allSettled([
        employeesService.list(workspaceId),
        deviceManagementService.listDevices(workspaceId),
        monitoringService.liveWall(workspaceId),
      ]);

      const employeeResult = results[0];
      const deviceResult = results[1];
      const monitoringResult = results[2];

      if (employeeResult.status === "fulfilled") {
        setEmployees(employeeResult.value.employees ?? []);
      } else {
        setEmployees([]);
      }

      if (deviceResult.status === "fulfilled") {
        setDevices(deviceResult.value.devices ?? []);
      } else {
        setDevices([]);
      }

      if (monitoringResult.status === "fulfilled") {
        setMonitoring(monitoringResult.value);
      } else {
        setMonitoring(null);
      }

      const failed = results.filter(
        (result) => result.status === "rejected",
      );

      if (failed.length > 0) {
        setError(
          "Some workspace monitoring data could not be loaded. " +
          "Check the backend service and your permissions.",
        );
      }'''

NEW_RESULTS = '''      const results = await Promise.allSettled([
        employeesService.list(workspaceId),
        deviceManagementService.listDevices(workspaceId),
        monitoringService.liveWall(workspaceId),
      ]);

      const employeeResult = results[0];
      const deviceResult = results[1];
      const monitoringResult = results[2];
      const notices: string[] = [];

      let workspaceEmployees: Employee[] = [];
      if (employeeResult.status === "fulfilled") {
        workspaceEmployees = Array.isArray(employeeResult.value.employees)
          ? employeeResult.value.employees
          : [];
      } else {
        notices.push(
          "Employee directory unavailable: " + messageFromError(employeeResult.reason),
        );
      }

      // Fallback only to another authenticated, workspace-scoped API.
      // Its monitoring.all/team/self permission checks remain enforced server-side.
      // Never manufacture employees from unscoped device records.
      if (workspaceEmployees.length === 0) {
        try {
          const scoped = await monitoringService.employees(workspaceId);
          const scopedRows = Array.isArray(scoped.items) ? scoped.items : [];
          workspaceEmployees = scopedRows.flatMap((row): Employee[] => {
            const id = typeof row.employee_id === "string"
              ? row.employee_id
              : typeof row.id === "string" ? row.id : "";
            const name = typeof row.name === "string"
              ? row.name
              : typeof row.employee === "string" ? row.employee : "";
            if (!id || !name) return [];
            // This normalized view is used only by the employee selector.
            return [{ id, full_name: name } as Employee];
          });
          if (workspaceEmployees.length > 0) {
            notices.length = 0;
          } else {
            notices.push("No employees returned by the authorized workspace APIs.");
          }
        } catch (cause) {
          notices.push(
            "Monitoring employee list unavailable: " + messageFromError(cause),
          );
        }
      }
      setEmployees(workspaceEmployees);

      if (deviceResult.status === "fulfilled") {
        const rows = deviceResult.value.devices;
        setDevices(Array.isArray(rows) ? rows : []);
        if (!Array.isArray(rows) || rows.length === 0) {
          notices.push("No registered devices returned by Device Management.");
        }
      } else {
        setDevices([]);
        notices.push(
          "Device Management unavailable: " + messageFromError(deviceResult.reason),
        );
      }

      if (monitoringResult.status === "fulfilled") {
        setMonitoring(monitoringResult.value);
      } else {
        setMonitoring(null);
        notices.push(
          "Monitoring summary unavailable: " + messageFromError(monitoringResult.reason),
        );
      }

      if (notices.length > 0) {
        setError(notices.join(" "));
      }'''

OLD_EMPTY = '''                  <option value="">Select employee</option>
                  {employees.map((employee) => ('''
NEW_EMPTY = '''                  <option value="">{employees.length === 0 ? "No available employees" : "Select employee"}</option>
                  {employees.map((employee) => ('''

OLD_NAME = '''                      {employee.full_name ||
                        `${employee.first_name} ${employee.last_name}`}'''
NEW_NAME = '''                      {employee.full_name ||
                        `${employee.first_name ?? ""} ${employee.last_name ?? ""}`.trim()}'''


def patch(source: str) -> str:
    if 'Monitoring employee list unavailable:' in source:
        return source
    for needle, label in ((OLD_RESULTS, 'employee/device loader'), (OLD_EMPTY, 'employee selector'), (OLD_NAME, 'employee display')):
        if source.count(needle) != 1:
            raise RuntimeError(f'Unexpected current frontend source ({label}); refusing to modify.')
    output = source.replace(OLD_RESULTS, NEW_RESULTS, 1).replace(OLD_EMPTY, NEW_EMPTY, 1).replace(OLD_NAME, NEW_NAME, 1)
    if output.count('monitoringService.employees(workspaceId)') != 1:
        raise RuntimeError('Safety validation failed')
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--root', type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    target = args.root / REL
    if not target.is_file():
        print(f'ERROR: Current frontend file not found: {target}')
        return 1
    before = target.read_text(encoding='utf-8-sig')
    try:
        after = patch(before)
    except RuntimeError as exc:
        print(f'ERROR: {exc}')
        return 1
    if before == after:
        print('ALREADY PATCHED. No changes needed.')
        return 0
    print('SOURCE LAYOUT: PASS')
    print('SCOPE: employee loading fallback + errors + selector label')
    print('AUTHORIZATION: unchanged; server enforces employee scope')
    print('REGISTERED DEVICE IDS: unchanged')
    print('LIVE VIDEO TRANSPORT: not modified / not implemented')
    if not args.apply:
        print('DRY RUN ONLY. Use --apply to write with backup.')
        return 0
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = target.with_name(target.name + '.backup-' + stamp)
    if backup.exists():
        print('ERROR: backup path exists; refusing to overwrite')
        return 1
    shutil.copy2(target, backup)
    target.write_text(after, encoding='utf-8')
    print(f'PATCH APPLIED: {target}')
    print(f'BACKUP: {backup}')
    print('NEXT: run frontend TypeScript check and refresh port 3001 page.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
