Set WshShell = CreateObject("WScript.Shell")

' === 통합 실행 Python 스크립트 경로 ===
pyPath = "E:\KR_US_INSTITUTIONAL_BOT\run_all_v5_plus.py"

' === 파이썬 실행 ===
cmd = "cmd /c python """ & pyPath & """"
WshShell.Run cmd, 1, False
