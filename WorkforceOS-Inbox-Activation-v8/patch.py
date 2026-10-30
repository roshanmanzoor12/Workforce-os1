from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(encoding="utf-8-sig"); before=s
s=s.replace('(s.Status == "requested" || s.Status == "active")','(s.Status == "requested" || s.Status == "accepted" || s.Status == "active")',1)
needle='                                await _client.ActivateAsync(credentials, item.SessionId, stoppingToken);\n                            }\n                            else continue;\n                        }\n\n                        // Recovery path'
replacement='                                var activatedStatus = await _client.ActivateAsync(credentials, item.SessionId, stoppingToken);\n                                if (activatedStatus != "active")\n                                {\n                                    _logger.LogWarning("Live-screen activation pending for {SessionId}: {Status}", item.SessionId, activatedStatus);\n                                    continue;\n                                }\n                            }\n                            else continue;\n                        }\n                        else if (item.Status == "accepted")\n                        {\n                            // Employee has already accepted. Retry activation, never fabricate approval.\n                            var activatedStatus = await _client.ActivateAsync(credentials, item.SessionId, stoppingToken);\n                            if (activatedStatus != "active")\n                            {\n                                _logger.LogWarning("Live-screen activation retry pending for {SessionId}: {Status}", item.SessionId, activatedStatus);\n                                continue;\n                            }\n                        }\n\n                        // Recovery path'
if needle in s: s=s.replace(needle,replacement,1)
elif "activation retry pending for" not in s: raise SystemExit("INCOMPATIBLE: activation block changed; refusing patch")
needle='                    var liveIds = valid.Select(s => s.SessionId).ToHashSet();'
replacement='                    _logger.LogInformation("Live-screen inbox poll: sessions={Count} consent={Consent} authorized={Authorized}", valid.Count, inbox.ConsentGranted, inbox.CaptureAuthorized);\n                    var liveIds = valid.Select(s => s.SessionId).ToHashSet();'
if "Live-screen inbox poll:" in s: pass
elif needle in s: s=s.replace(needle,replacement,1)
else: raise SystemExit("INCOMPATIBLE: inbox logging")
if '(s.Status == "requested" || s.Status == "accepted" || s.Status == "active")' not in s: raise SystemExit("INCOMPATIBLE: status filter")
if s!=before: p.write_text(s,encoding="utf-8")
print("PATCH_OK", "unchanged" if s==before else "modified")
