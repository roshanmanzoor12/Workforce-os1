# WorkforceOS Native Decision IPC (source-only)

This replaces the information-only Windows IPC popup with an **Accept / Decline** dialog and a bounded local pipe reply to the Windows Agent. The Agent records only a generic informational log message; it **does not submit a session decision to the backend** and **does not start capture**. This is deliberate until authenticated Windows-session binding, backend decision authorization and media delivery are implemented.

No Chrome screen chooser is involved. The source must be compiled on Windows; there is no dotnet SDK in this packaging environment.

`Apply.ps1` defaults to dry-run and validates SHA256 against the previously installed Native IPC Step. `-Apply` backs up four source files then replaces them. `-Rollback` restores from `.latest-backup.txt`. Do not deploy running Agent or Companion binaries on the basis of this patch.

**Still missing:** secure service-to-user binding, authenticated backend decision, Companion-to-Agent frame transfer, continuous video and owner playback. This ZIP is not a full live screen fix.
