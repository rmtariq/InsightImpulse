#!/usr/bin/env bash
# =============================================================================
# Crowding Approve — DFA slot booking (curl flow)
# Help desk / CA staff / agent-assisted queue reservation
#
# Usage:
#   cp scripts/crowding_approve/dfa_slot_booking.env.example .env.dfa
#   # edit .env.dfa (BASE_URL, TOKEN, branch, slot, user)
#   source .env.dfa && bash scripts/crowding_approve/dfa_slot_booking_curl.sh
#
# Or run step-by-step (see comments below).
# =============================================================================
set -euo pipefail

: "${BASE_URL:?Set BASE_URL e.g. https://api.crowding-approve.example}"
: "${AUTH_TOKEN:?Set AUTH_TOKEN (Bearer)}"

# --- Booking targets (adjust per case) ---
BRANCH_ID="${BRANCH_ID:-DFA-NCR-ASEANA}"
PROCESS_TYPE_ID="${PROCESS_TYPE_ID:-PASSPORT_NEW}"
SCHEDULE_DATE="${SCHEDULE_DATE:-2026-07-20}"
SLOT_ID="${SLOT_ID:-}"                    # from queue-process-config
SCHEDULE_TIME="${SCHEDULE_TIME:-09:00}"   # HH:MM if API uses time not slot_id
USER_ID="${USER_ID:-}"
CASE_ID="${CASE_ID:-}"
APPOINTMENT_TYPE="${APPOINTMENT_TYPE:-assisted}"  # walk_in | assisted | agent
AGENT_ID="${AGENT_ID:-}"                  # required if assisted by agent
STAFF_ID="${STAFF_ID:-}"                  # CA / help desk staff

API="${BASE_URL%/}"
AUTH_HEADER="Authorization: Bearer ${AUTH_TOKEN}"
CT_FORM="Content-Type: application/x-www-form-urlencoded"
CT_JSON="Content-Type: application/json"
OUT_DIR="${OUT_DIR:-/tmp/crowding_approve}"
mkdir -p "$OUT_DIR"

curl_json() {
  local method="$1" url="$2" out="$3"
  shift 3
  curl -sS -X "$method" "$url" \
    -H "$AUTH_HEADER" \
    -H "Accept: application/json" \
    "$@" \
    -o "$out" \
    -w "\nHTTP %{http_code}\n"
}

curl_form() {
  local method="$1" url="$2" out="$3"
  shift 3
  curl -sS -X "$method" "$url" \
    -H "$AUTH_HEADER" \
    -H "$CT_FORM" \
    -H "Accept: application/json" \
    "$@" \
    -o "$out" \
    -w "\nHTTP %{http_code}\n"
}

echo "=== Crowding Approve DFA booking flow ==="
echo "BASE_URL=$API"
echo "OUT_DIR=$OUT_DIR"
echo ""

# -----------------------------------------------------------------------------
# STEP 1 — Initial Data Load
# Fetches scheduling requirements for the authenticated user.
# Typical: branches, process types, document checklist, eligibility flags.
# -----------------------------------------------------------------------------
echo "▶ [1/5] GET /initial-data-load"
curl_json GET "${API}/initial-data-load" "${OUT_DIR}/01_initial_data_load.json"
echo "   saved: ${OUT_DIR}/01_initial_data_load.json"
echo ""

# Optional: POST variant if your deployment uses POST + user context
# curl_json POST "${API}/initial-data-load" "${OUT_DIR}/01_initial_data_load.json" \
#   -H "$CT_FORM" \
#   --data-urlencode "user_id=${USER_ID}"

# -----------------------------------------------------------------------------
# STEP 2 — Queue Process Configuration
# Branch + schedule queue config for selected process type.
# Use response to pick SLOT_ID / available times.
# -----------------------------------------------------------------------------
echo "▶ [2/5] GET /queue-process/queue-process-config"
QP_QUERY="process_type_id=${PROCESS_TYPE_ID}&branch_id=${BRANCH_ID}&schedule_date=${SCHEDULE_DATE}"
curl_json GET "${API}/queue-process/queue-process-config?${QP_QUERY}" \
  "${OUT_DIR}/02_queue_process_config.json"
echo "   saved: ${OUT_DIR}/02_queue_process_config.json"
echo ""

# POST variant (some builds expect form body):
# curl_form POST "${API}/queue-process/queue-process-config" "${OUT_DIR}/02_queue_process_config.json" \
#   --data-urlencode "process_type_id=${PROCESS_TYPE_ID}" \
#   --data-urlencode "branch_id=${BRANCH_ID}" \
#   --data-urlencode "schedule_date=${SCHEDULE_DATE}"

# Auto-pick first slot if jq available and SLOT_ID empty
if [[ -z "$SLOT_ID" ]] && command -v jq >/dev/null 2>&1; then
  SLOT_ID="$(jq -r '.slots[0].id // .available_slots[0].slot_id // .data.slots[0].id // empty' \
    "${OUT_DIR}/02_queue_process_config.json" 2>/dev/null || true)"
  if [[ -n "$SLOT_ID" && "$SLOT_ID" != "null" ]]; then
    echo "   auto SLOT_ID=$SLOT_ID"
  fi
fi

# -----------------------------------------------------------------------------
# STEP 3 — Case List (before booking — verify open case / profile)
# -----------------------------------------------------------------------------
echo "▶ [3/5] GET /case-list"
CASE_QUERY="user_id=${USER_ID}"
curl_json GET "${API}/case-list?${CASE_QUERY}" "${OUT_DIR}/03_case_list.json"
echo "   saved: ${OUT_DIR}/03_case_list.json"
echo ""

if [[ -z "$CASE_ID" ]] && command -v jq >/dev/null 2>&1; then
  CASE_ID="$(jq -r '.cases[0].id // .data[0].case_id // empty' \
    "${OUT_DIR}/03_case_list.json" 2>/dev/null || true)"
  if [[ -n "$CASE_ID" && "$CASE_ID" != "null" ]]; then
    echo "   auto CASE_ID=$CASE_ID"
  fi
fi

# -----------------------------------------------------------------------------
# STEP 4 — Make a Reservation (form-encoded full booking flow)
# This is the main DFA slot booking call.
# -----------------------------------------------------------------------------
echo "▶ [4/5] POST /make-a-reservation"

RESERVATION_DATA=(
  --data-urlencode "user_id=${USER_ID}"
  --data-urlencode "case_id=${CASE_ID}"
  --data-urlencode "branch_id=${BRANCH_ID}"
  --data-urlencode "process_type_id=${PROCESS_TYPE_ID}"
  --data-urlencode "schedule_date=${SCHEDULE_DATE}"
  --data-urlencode "appointment_type=${APPOINTMENT_TYPE}"
)

[[ -n "$SLOT_ID" ]] && RESERVATION_DATA+=(--data-urlencode "slot_id=${SLOT_ID}")
[[ -n "$SCHEDULE_TIME" ]] && RESERVATION_DATA+=(--data-urlencode "schedule_time=${SCHEDULE_TIME}")
[[ -n "$AGENT_ID" ]] && RESERVATION_DATA+=(--data-urlencode "agent_id=${AGENT_ID}")
[[ -n "$STAFF_ID" ]] && RESERVATION_DATA+=(--data-urlencode "staff_id=${STAFF_ID}")
[[ -n "${APPLICANT_FIRST_NAME:-}" ]] && RESERVATION_DATA+=(--data-urlencode "first_name=${APPLICANT_FIRST_NAME}")
[[ -n "${APPLICANT_LAST_NAME:-}" ]] && RESERVATION_DATA+=(--data-urlencode "last_name=${APPLICANT_LAST_NAME}")
[[ -n "${APPLICANT_EMAIL:-}" ]] && RESERVATION_DATA+=(--data-urlencode "email=${APPLICANT_EMAIL}")
[[ -n "${APPLICANT_MOBILE:-}" ]] && RESERVATION_DATA+=(--data-urlencode "mobile=${APPLICANT_MOBILE}")
[[ -n "${PASSPORT_TYPE:-}" ]] && RESERVATION_DATA+=(--data-urlencode "passport_type=${PASSPORT_TYPE}")
[[ -n "${PROCESSING_TYPE:-}" ]] && RESERVATION_DATA+=(--data-urlencode "processing_type=${PROCESSING_TYPE}")
[[ -n "${REMARKS:-}" ]] && RESERVATION_DATA+=(--data-urlencode "remarks=${REMARKS}")

curl_form POST "${API}/make-a-reservation" "${OUT_DIR}/04_make_a_reservation.json" \
  "${RESERVATION_DATA[@]}"
echo "   saved: ${OUT_DIR}/04_make_a_reservation.json"
echo ""

TICKET_ID=""
APPOINTMENT_ID=""
if command -v jq >/dev/null 2>&1; then
  TICKET_ID="$(jq -r '.ticket_id // .data.ticket_id // .ticket.id // empty' \
    "${OUT_DIR}/04_make_a_reservation.json" 2>/dev/null || true)"
  APPOINTMENT_ID="$(jq -r '.appointment_id // .data.appointment_id // .reservation_id // empty' \
    "${OUT_DIR}/04_make_a_reservation.json" 2>/dev/null || true)"
  [[ -n "$TICKET_ID" && "$TICKET_ID" != "null" ]] && echo "   ticket_id=$TICKET_ID"
  [[ -n "$APPOINTMENT_ID" && "$APPOINTMENT_ID" != "null" ]] && echo "   appointment_id=$APPOINTMENT_ID"
fi

# -----------------------------------------------------------------------------
# STEP 5 — Get Ticket (appointment confirmation)
# -----------------------------------------------------------------------------
echo "▶ [5/5] GET /get-ticket"
TICKET_QUERY=""
[[ -n "$TICKET_ID" ]] && TICKET_QUERY="ticket_id=${TICKET_ID}"
[[ -z "$TICKET_QUERY" && -n "$APPOINTMENT_ID" ]] && TICKET_QUERY="appointment_id=${APPOINTMENT_ID}"
[[ -z "$TICKET_QUERY" && -n "$USER_ID" ]] && TICKET_QUERY="user_id=${USER_ID}"

curl_json GET "${API}/get-ticket?${TICKET_QUERY}" "${OUT_DIR}/05_get_ticket.json"
echo "   saved: ${OUT_DIR}/05_get_ticket.json"
echo ""

echo "✅ Flow complete. Review JSON in: $OUT_DIR"
