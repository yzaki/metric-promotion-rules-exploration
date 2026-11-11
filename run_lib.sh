# Sourced by every run_*.sh: stop at the first failing command (including inside pipelines and background jobs),
# treat unset variables as errors, and provide waitall, which waits for each background job and fails if any did.
set -euo pipefail
waitall() {
  local rc=0 p
  for p in $(jobs -p); do wait "$p" || rc=$?; done
  if [ "$rc" != 0 ]; then echo "a background job failed (exit $rc); stopping" >&2; exit "$rc"; fi
}
