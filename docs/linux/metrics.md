# Linux 모니터링 지표(초안)

본 모듈은 리눅스 호스트의 핵심 시스템 지표를 경량 수집합니다.

- system: uptime_seconds, cpu_count, loadavg_1/5/15
- memory: MemTotal/Available(kB), SwapTotal/Free(kB) — `/proc/meminfo`
- disk: 루트(`/`) 디스크 total/used/free(bytes)
- network: 총 수신/송신 바이트 — `/proc/net/dev` 합계

주의
- 리눅스 `/proc` 의존. 일부 환경(컨테이너/특수 커널)에서 값이 제한될 수 있음.
- 상세 지표 확대(퍼센트, per-interface, per-mount)는 차기 버전 예정.


