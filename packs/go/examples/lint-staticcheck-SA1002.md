---
source: staticcheck
kind: lint
language: go
linter: staticcheck
rule: SA1002
tool_version: "v0.8.2"
available_since: "2017.1"
url: https://staticcheck.dev/docs/checks#SA1002
license: MIT
---

# SA1002: Invalid format in time.Parse

time.Parse requires a layout string that uses Go's reference time:
'Mon Jan 2 15:04:05 MST 2006'. The layout must represent this date and time
exactly. See https://pkg.go.dev/time#pkg-constants for layout examples.