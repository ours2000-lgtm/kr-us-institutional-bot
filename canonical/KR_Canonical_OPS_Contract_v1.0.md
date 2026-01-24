KR Canonical OPS Contract (LOCK) v1.0

Status: LOCKED (Canonical)
Market: KR (Korea)
Effective Date: 2026-01-24
Change Policy: LOCK 해제 또는 버전 상승(v2.0+) 없이는 변경 불가

0. 목적 (Purpose)

본 문서는 KR 자동매매 엔진의 운영(Start/Stop) 계층에 대한 Canonical OPS Contract를 정의한다.
여기서 정의된 규약은 **KR을 기준선(Canonical)**으로 하며,
US / CRYPTO 등 모든 파생 마켓은 본 문서를 그대로 복제한 후 이름·경로·파라미터만 치환해야 한다.

본 문서는 운영 안정성, 감사 추적성, 중복 실행 방지, 안전한 종료를 최우선 목표로 한다.

1. 적용 대상 (Applies To – Code Snapshot)

본 Canonical은 아래 코드 스냅샷에 적용된다.

파일	역할
common_env.bat	공통 환경 변수 정의 및 런타임 디렉토리 준비
start_kr.bat	KR 엔진 시작용 Batch Wrapper
start_kr.ps1	실제 프로세스 스폰 및 PID_JSON 기록
stop_kr.bat	STOP_FLAG 기반 Graceful / Force Stop
run_korea_v9_plus.py	KR 엔진 메인 엔트리 (Engine-side Contract 대상)

⚠️ 위 파일의 역할, 인터페이스, 의미는 LOCK 대상이다.

2. LOCK 대상 범위 (Canonical Scope)

아래 항목은 KR Canonical OPS Contract로서 동결되며,
명시적 LOCK 해제 또는 버전 개정 절차 없이는 변경될 수 없다.

2.1 실행 엔트리 포인트

start_kr.bat, start_kr.ps1, stop_kr.bat

common_env.bat의 공통 환경 초기화 역할

2.2 Runtime Contract
2.2.1 PID_JSON (Runtime Metadata)

필수 필드

{
  "pid": number,
  "script": string,
  "mode": "PAPER" | "LIVE",
  "started": "YYYY-MM-DD HH:mm:ss",
  "pid_json": string,
  "flag": string,
  "out_log": string,
  "err_log": string
}


선택(확장) 필드

{
  "host": string,
  "user": string,
  "cmdline": string,
  "exit_code": number,
  "heartbeat": "YYYY-MM-DD HH:mm:ss"
}


필수 필드는 모든 마켓에서 동일

선택 필드는 확장 가능하되 의미 변경 불가

2.2.2 STOP_FLAG

경로: runtime/flags/kr_stop.flag

의미: 엔진 종료 요청의 단일·최우선 트리거

STOP_FLAG 파일에는 최소 다음 정보가 기록된다.

[timestamp] STOP_REQUEST RUN_MODE=PAPER

2.3 Stop / Exit 정책
Exit Code Semantics (Canonical)
코드	의미
0	정상 종료 (Graceful) 또는 정책상 허용 상태
1	강제 종료 (Force Kill 수행)
2	실패 또는 검증 오류

확장 코드(3~6 등)는 운영 보조 정보로 허용되나,
Canonical 의미(0/1/2)는 유지되어야 한다.

2.4 Stop Sequence (고정 순서)

STOP_FLAG 생성

Graceful wait (엔진 자율 종료)

Soft kill

Hard kill (필요 시)

ExitCode 기록 및 로그 정리

3. Logging Contract
3.1 로그 분리 원칙
로그	역할
kr_launcher.log	Start / Stop 이벤트 및 오류
kr_engine.log	Engine stdout
kr_engine.error.log	Engine stderr
3.2 로그 레벨

[INFO] 정상 흐름

[WARN] 비정상 가능성

[ERROR] 즉시 조치 필요

4. Engine-side Contract (필수)

KR 엔진(run_korea_v9_plus.py)은 반드시 아래를 만족해야 한다.

--mode, --pid_json, --flag_path 인자를 필수로 수용

메인 루프 및 신규 주문 생성 전마다 STOP_FLAG 존재 여부 확인

STOP_FLAG 발견 시:

신규 주문 즉시 차단

필요한 정리 작업 수행

Clean Exit

STOP_FLAG 존재 중 신규 주문 발행은 Canonical 위반이다.

5. 파생 마켓 규칙 (Derivation Rule)

KR Canonical을 그대로 복제한다.

차이는 이름 / 경로 / 파라미터 값만 허용된다.

네이밍 예시
KR	US	CRYPTO
kr_engine.json	us_engine.json	crypto_engine.json
kr_stop.flag	us_stop.flag	crypto_stop.flag
kr_launcher.log	us_launcher.log	crypto_launcher.log

구조·의미·계약은 KR과 동일해야 한다.

6. Canonical 우선순위 규칙

KR Canonical과 파생 마켓 구현이 충돌할 경우
항상 KR Canonical이 우선한다.

Canonical과 다른 패턴을 도입하려면
Canonical 자체를 v2.0 이상으로 개정해야 한다.

7. LOCK 해제 및 개정 절차

LOCK 해제 또는 변경은 **버전 상승(v2.0+)**을 통해서만 가능

변경 시 반드시:

변경 사유 명시

영향 범위 기록

Revision History 갱신

8. Revision History
Version	Date	Description
v1.0	2026-01-24	Initial KR Canonical OPS Contract LOCK

END OF DOCUMENT