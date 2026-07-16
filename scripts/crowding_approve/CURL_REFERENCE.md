# Crowding Approve — DFA Slot Booking (curl reference)

Sistem queue/booking DFA untuk **help desk**, **CA staff**, dan **agent**. Aliran penuh: muat data awal → config queue → semak case → book slot → ambil ticket.

Gantikan `BASE_URL`, `TOKEN`, dan field mengikut environment anda.

---

## 0. Pembolehubah

```bash
export BASE_URL="https://api.crowding-approve.example/v1"
export TOKEN="YOUR_BEARER_TOKEN"
export USER_ID="usr_abc123"
export BRANCH_ID="DFA-NCR-ASEANA"
export PROCESS_TYPE_ID="PASSPORT_NEW"
export SCHEDULE_DATE="2026-07-20"
export SLOT_ID="slot_20260720_0900"
export APPOINTMENT_TYPE="assisted"   # walk_in | assisted | agent
export AGENT_ID="agent_001"
export STAFF_ID="ca_staff_042"
```

---

## 1. Initial Data Load

Memuat keperluan penjadualan untuk pengguna yang diautentikasi (cawangan, jenis proses, checklist).

```bash
curl -sS -X GET "${BASE_URL}/initial-data-load" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" | jq .
```

**POST** (jika backend perlukan `user_id`):

```bash
curl -sS -X POST "${BASE_URL}/initial-data-load" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  --data-urlencode "user_id=${USER_ID}" | jq .
```

---

## 2. Queue Process Config

Konfigurasi queue cawangan/jadual untuk jenis proses dipilih.

```bash
curl -sS -X GET "${BASE_URL}/queue-process/queue-process-config" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" \
  --get \
  --data-urlencode "process_type_id=${PROCESS_TYPE_ID}" \
  --data-urlencode "branch_id=${BRANCH_ID}" \
  --data-urlencode "schedule_date=${SCHEDULE_DATE}" | jq .
```

**POST form-encoded:**

```bash
curl -sS -X POST "${BASE_URL}/queue-process/queue-process-config" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  --data-urlencode "process_type_id=${PROCESS_TYPE_ID}" \
  --data-urlencode "branch_id=${BRANCH_ID}" \
  --data-urlencode "schedule_date=${SCHEDULE_DATE}" | jq .
```

Ambil `slot_id` dari respons (contoh: `.slots[0].id`).

---

## 3. Case List

Senarai case dikaitkan dengan profil pengguna.

```bash
curl -sS -X GET "${BASE_URL}/case-list" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" \
  --get \
  --data-urlencode "user_id=${USER_ID}" | jq .
```

---

## 4. Make a Reservation (booking slot DFA)

**Endpoint utama** — payload `application/x-www-form-urlencoded`.

### Walk-in (self)

```bash
curl -sS -X POST "${BASE_URL}/make-a-reservation" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  --data-urlencode "user_id=${USER_ID}" \
  --data-urlencode "branch_id=${BRANCH_ID}" \
  --data-urlencode "process_type_id=${PROCESS_TYPE_ID}" \
  --data-urlencode "schedule_date=${SCHEDULE_DATE}" \
  --data-urlencode "slot_id=${SLOT_ID}" \
  --data-urlencode "schedule_time=09:00" \
  --data-urlencode "appointment_type=walk_in" \
  --data-urlencode "first_name=Juan" \
  --data-urlencode "last_name=Dela Cruz" \
  --data-urlencode "email=juan@example.com" \
  --data-urlencode "mobile=+639171234567" \
  --data-urlencode "passport_type=regular" \
  --data-urlencode "processing_type=regular" | jq .
```

### Agent / CA staff assisted

```bash
curl -sS -X POST "${BASE_URL}/make-a-reservation" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Accept: application/json" \
  --data-urlencode "user_id=${USER_ID}" \
  --data-urlencode "case_id=${CASE_ID}" \
  --data-urlencode "branch_id=${BRANCH_ID}" \
  --data-urlencode "process_type_id=${PROCESS_TYPE_ID}" \
  --data-urlencode "schedule_date=${SCHEDULE_DATE}" \
  --data-urlencode "slot_id=${SLOT_ID}" \
  --data-urlencode "appointment_type=assisted" \
  --data-urlencode "agent_id=${AGENT_ID}" \
  --data-urlencode "staff_id=${STAFF_ID}" \
  --data-urlencode "first_name=Juan" \
  --data-urlencode "last_name=Dela Cruz" \
  --data-urlencode "email=juan@example.com" \
  --data-urlencode "mobile=+639171234567" \
  --data-urlencode "remarks=Booked via help desk Crowding Approve" | jq .
```

Simpan `ticket_id` / `appointment_id` dari respons.

---

## 5. Get Ticket

Butiran tiket / appointment selepas booking.

```bash
curl -sS -X GET "${BASE_URL}/get-ticket" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" \
  --get \
  --data-urlencode "ticket_id=${TICKET_ID}" | jq .
```

Alternatif query:

```bash
# by appointment_id
curl -sS -X GET "${BASE_URL}/get-ticket?appointment_id=${APPOINTMENT_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" | jq .

# latest for user
curl -sS -X GET "${BASE_URL}/get-ticket?user_id=${USER_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" | jq .
```

---

## Aliran satu perintah (skrip)

```bash
source .env.dfa
bash scripts/crowding_approve/dfa_slot_booking_curl.sh
```

Respons disimpan di `/tmp/crowding_approve/01_*.json` … `05_*.json`.

---

## Nota integrasi (`modules/reservation`, `modules/queue-process`)

| Modul | Endpoint | Peranan |
|-------|----------|---------|
| reservation | `/initial-data-load`, `/make-a-reservation`, `/get-ticket`, `/case-list` | Booking & pengesahan |
| queue-process | `/queue-process/queue-process-config` | Slot & konfigurasi cawangan |

Jika field sebenar berbeza (nama key JSON/form), laraskan `--data-urlencode` mengikut kontrak API production anda.
