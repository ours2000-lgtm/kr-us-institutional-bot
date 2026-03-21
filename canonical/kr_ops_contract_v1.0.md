# KR Canonical OPS Contract — LOCK v1.0

Status: LOCK (Canonical)
Version: v1.0
Effective Date: 2026-01-24 (KST)
Scope: KR market + all derived markets (US, CRYPTO, ...)

---

## 0. Purpose

This document defines the **canonical** operational contract for starting/stopping the KR engine.
It is the single source of truth for launcher/stopper behavior, runtime artifacts, and exit-code semantics.
All derived markets MUST follow this contract unless a formal LOCK revision is executed.

---

## 1. Applies To (Code Snapshot)

The following artifacts are LOCKED under this contract:

- `ops/launcher/common_env.bat`  
  Role: Common environment variables + runtime/log directory provisioning

- `ops/launcher/start_kr.bat`  
  Role: KR start entry wrapper (calls common_env + delegates to start_kr.ps1)

- `ops/launcher/start_kr.ps1`  
  Role: Process spawn + PID_JSON write (atomic) + runtime contract injection

- `ops/launcher/stop_kr.bat`  
  Role: STOP_FLAG-first graceful stop, then force-kill fallback

- `v9_core/run_korea_v9_plus.py`  
  Role: KR engine entry; MUST honor engine-side contract (CLI + STOP_FLAG polling)

> NOTE: Runtime-generated artifacts (logs/, runtime/pids/, runtime/flags/) are NOT part of this code snapshot.

---

## 2. LOCK Scope

The following items are frozen and MUST NOT change without formal revision:

### 2.1 Entry Points & Roles
- File names and roles of:
  - `common_env.bat`
  - `start_kr.bat`
  - `start_kr.ps1`
  - `stop_kr.bat`

### 2.2 Runtime Contract
- PID JSON path:
  - `runtime/pids/kr_engine.json`
- STOP FLAG path:
  - `runtime/flags/kr_stop.flag`
- Engine CLI arguments (names + meanings):
  - `--mode`      : PAPER | LIVE
  - `--pid_json`  : path to PID JSON artifact
  - `--flag_path` : path to STOP flag artifact

### 2.3 Stop / Exit Policy (Semantic)
Stopper MUST follow:
1) create STOP_FLAG
2) wait graceful shutdown (poll)
3) if still alive → force kill
4) emit final exit code

Exit codes (CANONICAL):
- `0` = graceful stop OR policy-allowed “nothing to stop”
- `1` = force kill executed (process terminated forcibly)
- `2` = failure (verification error, permission, kill failure, etc.)

### 2.4 Logging Contract
Logs are separated by role:
- Launcher log: `logs/kr_launcher.log` (start/stop events + errors)
- Engine stdout: `logs/kr_engine.log`
- Engine stderr: `logs/kr_engine.error.log`

Log levels MUST use:
- `[INFO]`, `[WARN]`, `[ERROR]`

---

## 3. PID_JSON Schema

### 3.1 Required Fields
- `pid`      : number
- `script`   : string
- `mode`     : "PAPER" | "LIVE"
- `started`  : string (format: `YYYY-MM-DD HH:mm:ss`)
- `pid_json` : string (path)
- `flag`     : string (path)
- `out_log`  : string (path)
- `err_log`  : string (path)

### 3.2 Optional Fields (Allowed Extensions)
- `host`         : string
- `user`         : string
- `cmdline`      : string
- `launcher_ver` : string
- `python_ver`   : string
- `exit_code`    : number
- `heartbeat`    : string

> Rule: Derived markets may add optional fields, but MUST NOT remove or rename required fields.

---

## 4. STOP_FLAG Contract

- STOP_FLAG existence is the highest-priority stop trigger.
- STOP_FLAG may contain a human-readable line including timestamp and reason.
- While STOP_FLAG exists, the engine MUST NOT generate new orders.

---

## 5. Engine-side Contract (Mandatory)

`run_korea_v9_plus.py` MUST:
- accept `--mode`, `--pid_json`, `--flag_path`
- poll STOP_FLAG at least once per main loop (and before creating new orders)
- upon STOP_FLAG detection:
  - block new orders immediately
  - perform necessary cleanup
  - exit cleanly (graceful)

Any engine change that violates this contract is considered a LOCK violation and requires formal revision.

---

## 6. Canonical Priority Rule

If any derived market implementation conflicts with this KR canonical contract:
- KR canonical contract ALWAYS WINS.
- The derived market MUST be modified to match KR.
- Introducing a different pattern requires revising this canonical contract first (v1.1, v2.0, ...).

---

## 7. Revision & Unlock Procedure

### 7.1 Versioning
- Any change to LOCK scope MUST increment version (v1.1, v1.2, ...).
- A revision entry MUST be recorded below.

### 7.2 Unlock / Change Approval (Minimum)
- OPS Lead approval + Audit reviewer approval
- Change record must reference:
  - reason
  - diff summary
  - effective date
  - new version

### 7.3 Revision History
- v1.0 — 2026-01-24 — Initial KR Canonical OPS Contract declared (LOCK)
