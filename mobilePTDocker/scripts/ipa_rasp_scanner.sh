#!/bin/bash
#
# Static iOS RASP Scanner for IPA files
# Integrated into Bellion mobilePTDocker.
# Pure static analysis — no device or Frida required.
#
# Detects common RASP / anti-RE indicators:
#   - Anti-debug (ptrace, PT_DENY_ATTACH, sysctl, getppid, P_TRACED)
#   - Jailbreak detection (Cydia, Substrate, paths, URL schemes, method names)
#   - Instrumentation detection (Frida, Cycript, dyld image scanning)
#
# Usage (inside mobilePTDocker):
#   ipa-rasp /workspace/app.ipa
#   ipa-rasp /workspace/app.ipa --json
#
# Output: Human-readable report (default) or JSON.
#

set -euo pipefail

IPA_FILE="${1:-}"
OUTPUT_JSON=false

if [[ -z "$IPA_FILE" || ! -f "$IPA_FILE" ]]; then
  echo "Usage: ipa-rasp <path-to.ipa> [--json]"
  echo "Example: ipa-rasp /workspace/MyApp.ipa"
  exit 1
fi

if [[ "${2:-}" == "--json" ]]; then
  OUTPUT_JSON=true
fi

TMP_DIR=$(mktemp -d /tmp/ipa_rasp_XXXXXX)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "[*] Extracting IPA: $(basename "$IPA_FILE")"
unzip -q "$IPA_FILE" -d "$TMP_DIR" || { echo "[!] Failed to unzip IPA"; exit 1; }

APP_DIR=$(find "$TMP_DIR" -type d -name "*.app" | head -1)
if [[ -z "$APP_DIR" ]]; then
  echo "[!] No .app bundle found in IPA"
  exit 1
fi

BINARY_NAME=$(basename "$APP_DIR" .app)
BINARY="$APP_DIR/$BINARY_NAME"

if [[ ! -f "$BINARY" ]]; then
  BINARY=$(find "$APP_DIR" -type f -name "$BINARY_NAME" | head -1)
fi

if [[ ! -f "$BINARY" ]]; then
  echo "[!] Main binary not found inside .app"
  exit 1
fi

echo "[*] Analyzing binary: $(basename "$BINARY")"
echo ""

# ---------- Findings collector ----------
declare -a FINDINGS=()

add_finding() {
  local category="$1"
  local severity="$2"
  local evidence="$3"
  FINDINGS+=("$category|$severity|$evidence")
}

# ---------- String-based checks ----------
echo "[*] Scanning strings for RASP indicators..."

STRINGS_OUT="$TMP_DIR/strings.txt"
strings -a "$BINARY" > "$STRINGS_OUT" 2>/dev/null || true

check_string() {
  local pattern="$1"
  local category="$2"
  local severity="$3"
  if grep -qF "$pattern" "$STRINGS_OUT" 2>/dev/null; then
    local matches
    matches=$(grep -oF "$pattern" "$STRINGS_OUT" | head -3 | tr '\n' ',' | sed 's/,$//')
    add_finding "$category" "$severity" "String match: $pattern (examples: $matches)"
    return 0
  fi
  return 1
}

# Anti-debug
check_string "ptrace" "Anti-Debug" "High" || true
check_string "PT_DENY_ATTACH" "Anti-Debug" "High" || true
check_string "sysctl" "Anti-Debug" "Medium" || true
check_string "getppid" "Anti-Debug" "Medium" || true
check_string "P_TRACED" "Anti-Debug" "High" || true
check_string "KERN_PROC" "Anti-Debug" "Medium" || true
check_string "isDebugged" "Anti-Debug" "Medium" || true

# Jailbreak
check_string "Cydia" "Jailbreak Detection" "High" || true
check_string "MobileSubstrate" "Jailbreak Detection" "High" || true
check_string "/bin/bash" "Jailbreak Detection" "High" || true
check_string "/usr/sbin/sshd" "Jailbreak Detection" "High" || true
check_string "cydia://" "Jailbreak Detection" "High" || true
check_string "sileo" "Jailbreak Detection" "Medium" || true
check_string "isJailbroken" "Jailbreak Detection" "High" || true
check_string "amIJailbroken" "Jailbreak Detection" "High" || true
check_string "detectJailbreak" "Jailbreak Detection" "High" || true

# Instrumentation
check_string "frida-server" "Instrumentation Detection" "High" || true
check_string "FridaGadget" "Instrumentation Detection" "High" || true
check_string "cycript" "Instrumentation Detection" "Medium" || true
check_string "SSLKillSwitch" "Instrumentation Detection" "Medium" || true
check_string "_dyld_get_image_name" "Instrumentation Detection" "Medium" || true
check_string "_dyld_image_count" "Instrumentation Detection" "Medium" || true

# ---------- Symbol checks ----------
if command -v nm >/dev/null 2>&1; then
  echo "[*] Checking unresolved symbols..."
  if nm -u "$BINARY" 2>/dev/null | grep -E 'ptrace|sysctl|getppid' >/dev/null; then
    add_finding "Anti-Debug" "High" "Unresolved symbols for ptrace/sysctl/getppid detected"
  fi
fi

# ---------- Info.plist checks ----------
INFO_PLIST="$APP_DIR/Info.plist"
if [[ -f "$INFO_PLIST" ]] && command -v plistutil >/dev/null 2>&1; then
  if plistutil -i "$INFO_PLIST" -o - 2>/dev/null | grep -qiE 'jailbreak|frida|cydia|substrate'; then
    add_finding "Configuration" "Low" "Suspicious strings found in Info.plist"
  fi
fi

# ---------- Output ----------
echo ""
echo "=========================================="
echo " iOS RASP Static Analysis Report"
echo "=========================================="
echo "IPA:     $(basename "$IPA_FILE")"
echo "Binary:  $(basename "$BINARY")"
echo "Findings: ${#FINDINGS[@]}"
echo ""

if [[ ${#FINDINGS[@]} -eq 0 ]]; then
  echo "[*] No common RASP indicators detected."
  echo "    (Binary may be obfuscated, or checks are implemented differently.)"
else
  printf "%-28s %-8s %s\n" "Category" "Severity" "Evidence"
  echo "------------------------------------------------------------------------"
  for f in "${FINDINGS[@]}"; do
    IFS='|' read -r cat sev evid <<< "$f"
    printf "%-28s %-8s %s\n" "$cat" "$sev" "$evid"
  done
fi

echo ""
echo "Notes:"
echo "- High severity: Strong static indicator of RASP / anti-RE controls."
echo "- Medium: Possible detection logic present."
echo "- This is static analysis only. Dynamic confirmation requires a device + Frida."
echo "- Commercial RASP (freeRASP, Guardsquare, etc.) often uses obfuscated or delayed checks."
echo ""

# JSON output
if [[ "$OUTPUT_JSON" == "true" ]]; then
  echo "=== JSON ==="
  echo "{"
  echo "  \"ipa\": \"$(basename "$IPA_FILE")\","
  echo "  \"binary\": \"$(basename "$BINARY")\","
  echo "  \"findings_count\": ${#FINDINGS[@]},"
  echo "  \"findings\": ["
  for i in "${!FINDINGS[@]}"; do
    IFS='|' read -r cat sev evid <<< "${FINDINGS[$i]}"
    comma=","
    [[ $i -eq $((${#FINDINGS[@]}-1)) ]] && comma=""
    evid_esc=$(echo "$evid" | sed 's/"/\\"/g')
    echo "    {\"category\": \"$cat\", \"severity\": \"$sev\", \"evidence\": \"$evid_esc\"}$comma"
  done
  echo "  ]"
  echo "}"
  echo ""
fi

echo "[*] Scan complete."
echo "    Next steps: unzip the IPA, inspect Info.plist with plistutil, or use Frida on a device for dynamic confirmation."
