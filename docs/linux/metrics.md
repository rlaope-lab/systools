# Linux 모니터링 지표

리눅스 호스트의 핵심 시스템 지표를 `/proc` 기반으로 경량 수집합니다.

## System
- uptime_seconds: 호스트 업타임(초) — `/proc/uptime`
- cpu_count: 논리 코어 수
- loadavg_1/5/15: 시스템 로드 평균 — `os.getloadavg()`
- cpu_usage_percent: 짧은 샘플(기본 200ms)로 계산한 CPU 사용률 — `/proc/stat`
- process_count: 현재 프로세스 개수 — `/proc` 디렉터리 내 PID 개수

## Memory
- mem_total_kb, mem_available_kb — `/proc/meminfo`
- mem_used_kb, mem_used_percent
- swap_total_kb, swap_free_kb, swap_used_kb, swap_used_percent

## Disk
- 마운트별 사용량(물리 FS 위주: ext2/3/4, xfs, btrfs, zfs)
  - {mount}.total_bytes, used_bytes, free_bytes, used_percent — `shutil.disk_usage`

## Network
- rx_bytes_total, tx_bytes_total — `/proc/net/dev` 합계
- interfaces: 인터페이스별 {rx_bytes, rx_packets, tx_bytes, tx_packets}

## File system
- fd_allocated, fd_max — `/proc/sys/fs/file-nr`

## Meta
- timestamp, node(hostname), kernel(uname 전체 문자열)

주의
- `/proc` 의존으로 일부 컨테이너/보안 환경에서 접근이 제한될 수 있습니다.
- CPU%는 짧은 샘플링 기반으로 약간의 지연(기본 ~200ms)을 유발합니다.


