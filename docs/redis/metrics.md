# Redis 모니터링 지표 설명서 (33선)

이 문서는 본 프로젝트가 수집하는 Redis 핵심 지표 33선에 대해, 지표 정의/의미/주의 임계 등을 한국어로 정리합니다. 지표는 Redis `INFO`, `CLIENT LIST`, `MEMORY MALLOC-STATS`, `CLUSTER INFO/SLOTS`, `PING` 기반 측정으로 수집됩니다.

## 권장 기준/안정 범위(일반 가이드)
- 환경·워크로드에 따라 달라질 수 있으니 초기에는 넓게 관찰 후, 본 가이드를 출발점으로 팀 기준을 조정하세요.
- 하단 상세 설명 각 항목에도 관련 코멘트를 병기했습니다.

- 성능
  - latency_ms: 일반 트래픽 하에서 0.2~1ms, 스파이크 3ms 미만 유지 권장
  - instantaneous_ops_per_sec: 절대값 기준 없음(서비스 SLO 대비 추세 안정이 중요)
  - hit_rate: 0.95(95%) 이상 권장, 0.90 미만 지속 시 개선 필요
  - total_commands_processed: 절대값 기준 없음(증가율 급등 시 원인 점검)
  - expired_keys: 트래픽/키수 대비 완만한 증가, 급증 시 TTL 재점검
- 메모리
  - mem_fragmentation_ratio: 1.0~1.2 양호, 1.2~1.4 주의, 1.4+ 튜닝/재시작 검토
  - used_memory vs maxmemory: 여유 20~30% 유지 권장(워크로드 특성에 따라 조정)
  - evicted_keys: 지속적 증가가 보이면 즉시 원인 분석(정상은 0에 수렴)
- 영속성
  - rdb_last_save_time: 정책 주기 내 정상 갱신(지연 시 디스크/I/O 점검)
  - rdb_changes_since_last_save: 정책 임계 이하 유지(스냅샷 직전 과도 증가 주의)
  - aof_last_write_status: 항상 ok, err 발생 즉시 장애
- 네트워크
  - connected_clients: 서비스 평시 기준선±20% 내 변동, 급증 시 커넥션 관리 점검
  - blocked_clients: 평시 0, 일시적 1+ 발생 시 즉시 확인
  - input/output_buffer_length: 평시 0~수십KB, 지속 증가 시 병목 신호
- CPU
  - used_cpu_sys/user: 절대값보다 증가 기울기 관찰, 코어 대비 60~70% 상시 점유면 원인 분석
- 클러스터/장애
  - cluster_state: 항상 ok
  - cluster_slots_assigned: 16384 전량 할당 상태 유지
  - cluster_slots_pfail/fail: 항상 0
  - master_link_status: up 유지, master_last_io_seconds_ago: 평시 수초 내
  - repl_backlog_size: 트래픽 대비 충분(재접속 시 partial resync 가능한 수준)

## 1. 성능(PERFORMANCE) 지표 7선

1) instantaneous_ops_per_sec  
- 정의: 최근 순간 처리량(초당 처리 요청 수, QPS)의 추정치  
- 의미: 현재 Redis가 어느 정도의 요청을 처리 중인지 나타내는 핵심 속도 지표  
- 참고: 급격한 하락은 병목(네트워크/CPU/디스크/락) 신호일 수 있음
 - 안정 범위: 절대 기준 없음. 서비스 SLO 내 지연을 유지하는 수준에서 추세가 안정적이면 양호

2) latency_ms (PING 기반)  
- 정의: `PING` 명령 왕복 시간의 평균(ms)  
- 의미: 클라이언트 관점에서의 응답 지연. 네트워크/서버 부하/블로킹 작업의 영향을 받음  
- 가이드: 1ms 이상 간헐적 급등(스파이크)이 지속되면 위험 신호
 - 안정 범위: 평시 0.2~1ms, 스파이크 3ms 미만. 워낙 저지연 환경에서는 0.2ms 전후도 가능

3) total_commands_processed  
- 정의: Redis 시작 이후 누적 처리된 명령 수  
- 의미: 전체 트래픽 추세 파악. 급격한 증가율은 트래픽 급증 또는 비정상 루프/스파이크 가능성
 - 안정 범위: 절대 기준 없음. 평시 증가 기울기 범위 내면 정상

4) keyspace_hits  
- 정의: 캐시에서 키 조회 성공 횟수  
- 의미: 캐시 적중량. `hits`가 높을수록 캐시 효율이 좋은 편

5) keyspace_misses  
- 정의: 캐시에서 키 조회 실패 횟수  
- 의미: 캐시 미스량. 미스가 높으면 백엔드(DB, API) 부하 증가 가능

6) hit_rate = hits / (hits + misses)  
- 정의: 캐시 적중률(0~1)  
- 의미: 캐시 품질 핵심 지표  
- 가이드: 0.9(90%) 이하가 지속되면 키 만료/적재 정책, 데이터 분포, 패턴(랜덤 키 접근) 튜닝 필요
 - 안정 범위: 0.95 이상 권장. 0.90 미만 지속은 개선 필요

7) expired_keys  
- 정의: TTL 만료로 제거된 키 수(누적)  
- 의미: TTL 정책이 의도대로 적용되는지 추적. 급증 시 만료 전략/데이터 신선성 점검
 - 안정 범위: 트래픽/키수 대비 완만한 증가. 급증 시 TTL/워크로드 재검토

## 2. 메모리(MEMORY) 지표 7선

8) used_memory  
- 정의: Redis가 관리하는 전체 메모리 사용량(bytes)  
- 의미: 현재 워킹셋 크기. 증가 추세와 피크 대비 여유를 관찰
 - 안정 범위: maxmemory 대비 70~80% 이하 유지 권장(버퍼·스파이크 고려)

9) used_memory_rss  
- 정의: 실제 OS 레벨의 물리 메모리 점유(bytes)  
- 의미: `used_memory`와 차이가 크면 파편화 또는 오버헤드 의심
 - 안정 범위: used_memory와 근접(±20% 내). 상회 폭이 크면 파편화 가능

10) used_memory_peak  
- 정의: 관측된 피크 메모리 사용량(bytes)  
- 의미: 최악 시나리오 대비 용량 설계/알람 기준 참고
 - 안정 범위: maxmemory 하회 유지. 피크가 자주 근접하면 용량 증설 또는 압축/만료 조정

11) mem_fragmentation_ratio = used_memory_rss / used_memory  
- 정의: 메모리 파편화 지표(비율)  
- 가이드: 1.0에 가까울수록 이상적. 1.4 이상이면 파편화 심각 → 재시작/할당자 튜닝 검토
 - 안정 범위: 1.0~1.2 양호, 1.2~1.4 주의, 1.4+ 조치 필요

12) maxmemory  
- 정의: Redis에 설정된 최대 메모리 제한(bytes)  
- 의미: 제한이 없으면 OS OOM Kill 위험. 운영 환경에서는 설정 권장
 - 안정 범위: 운영 필수 설정. 워킹셋+여유(20~30%)+버퍼를 고려해 산정

13) evicted_keys  
- 정의: 메모리 부족으로 제거된 키 수(누적)  
- 의미: 등장 즉시 원인 분석 필요(메모리 한계, eviction 정책, 키 크기/TTL 전략 조정)
 - 안정 범위: 정상은 0에 수렴. 지속 발생 시 즉시 원인 분석

14) allocator_stats  
- 정의: jemalloc 등 내부 메모리 할당자 통계 텍스트  
- 의미: 파편화/슬랩 크기/arena 등 메모리 내부 구조 분석에 활용
 - 안정 범위: 정량 기준보단 경향 분석(큰 단편화/슬랩 편향 여부 확인)

## 3. 스토리지/영속성(PERSISTENCE) 지표 5선

15) rdb_last_save_time  
- 정의: 마지막 RDB 스냅샷 저장 시각(UNIX epoch)  
- 의미: 지연 시 디스크 병목/백그라운드 저장 실패 가능성
 - 안정 범위: 정책 주기 내 최신으로 갱신

16) rdb_changes_since_last_save  
- 정의: 마지막 save 이후 변경된 키 수  
- 의미: 값이 너무 크면 스냅샷 시 지연/부하 위험. 스냅샷 주기/조건 재검토
 - 안정 범위: 정책 임계 이내(환경 의존). 스냅샷 직전 과도 증가 주의

17) aof_current_size  
- 정의: 현재 AOF 파일 크기(bytes)  
- 의미: 증가 추세가 빠르면 rewrite 정책/주기 점검 필요
 - 안정 범위: rewrite 정책에 따라 선형 완만 증가. 급격 증가/무한 팽창 방지

18) aof_base_size  
- 정의: 마지막 rewrite 후의 AOF 기준 크기(bytes)  
- 의미: 현재 크기와 비교해 AOF 팽창 여부 확인
 - 안정 범위: current 대비 과도한乂(배수 급증) 시 정책/워크로드 점검

19) aof_last_write_status  
- 정의: 마지막 AOF 쓰기 상태(ok/err)  
- 의미: 실패 발생 시 즉시 디스크/권한/파일시스템 문제 조사
 - 안정 범위: 항상 ok

## 4. 네트워크(NETWORK) 지표 4선

20) connected_clients  
- 정의: 현재 연결된 클라이언트 수  
- 의미: 증가 추세는 병목 신호. 커넥션 풀/타임아웃/장기 대기 연결 점검
 - 안정 범위: 평시 기준선±20% 내. 급증 시 커넥션 관리 점검

21) blocked_clients  
- 정의: BLPOP/BRPOP/WAIT 등 블로킹 명령으로 대기 중인 클라이언트 수  
- 의미: 값이 1 이상 지속되면 즉시 원인 분석(블로킹 패턴, 느린 소비자)
 - 안정 범위: 평시 0. 일시적 1+는 즉시 확인

22) input_buffer_length  
- 정의: `CLIENT LIST` 기반 입력 버퍼 총합(추정, bytes)  
- 의미: 증가 시 네트워크 정체/서버 처리 지연 의심
 - 안정 범위: 평시 0~수십KB 수준(환경 의존). 지속 증가 시 병목

23) output_buffer_length  
- 정의: `CLIENT LIST` 기반 출력 버퍼 총합(추정, bytes)  
- 의미: 증가 시 응답이 밀리고 있음을 의미. 소비자 측 병목/네트워크 이슈 가능
 - 안정 범위: 평시 0~수십KB 수준. 지속 증가/급등 시 네트워크/소비자 점검

## 5. CPU / 시스템(SYSTEM) 지표 4선

24) used_cpu_sys  
- 정의: Redis 서버 프로세스의 시스템 CPU 사용 누적(초)  
 - 안정 범위: 절대값보다 증가율 관찰. 코어 대비 60~70% 상시 점유면 원인 분석

25) used_cpu_user  
- 정의: Redis 서버 프로세스의 사용자 CPU 사용 누적(초)  
 - 안정 범위: 위와 동일

26) used_cpu_sys_children  
- 정의: 자식 프로세스의 시스템 CPU 사용 누적(초)  
 - 안정 범위: RDB/AOF 백그라운드 작업 시 일시 상승 가능. 장기 고점은 점검

27) used_cpu_user_children  
- 정의: 자식 프로세스의 사용자 CPU 사용 누적(초)  
 - 안정 범위: 위와 동일

- 공통 의미: CPU가 높으면 Lua 스크립트, Big Key, 무거운 정렬/스캔(SCAN, SORT), 느린 I/O가 의심 대상

## 6. 장애·클러스터(CLUSTER / FAILURE) 지표 6선

28) master_link_status  
- 정의: 레플리카 인스턴스에서 마스터와의 링크 상태(up/down)  
- 의미: down이면 복제 중단. 네트워크/보안/구성 점검
 - 안정 범위: up 유지

29) master_last_io_seconds_ago  
- 정의: 마스터로부터 마지막 I/O 이후 경과 시간(초)  
- 의미: 값이 커지면 동기화 지연. 링크 상태, backlog, 네트워크 확인
 - 안정 범위: 평시 수초 내, 장기 증가 시 점검

30) repl_backlog_size  
- 정의: 레플리케이션 백로그 버퍼 크기(bytes)  
- 의미: 충분하지 않으면 연결 문제 시 재동기화(full resync) 빈번
 - 안정 범위: 트래픽·RTT 대비 충분. 재연결 시 partial resync가 안정적으로 되는 수준

31) cluster_state  
- 정의: 클러스터 전체 상태(ok/fail)  
- 의미: fail이면 즉시 슬롯 할당/노드 상태/네트워크 점검
 - 안정 범위: 항상 ok

32) cluster_slots_assigned  
- 정의: 클러스터에서 할당된 슬롯 수(0~16384)  
- 의미: 전체 슬롯이 정상적으로 배정되어야 ok 상태 유지
 - 안정 범위: 16384 전량 할당

33) cluster_slots_pfail, cluster_slots_fail  
- 정의: 파셜 실패/완전 실패 상태의 슬롯 수  
- 의미: 값이 0이 아니면 실패 중인 노드/슬롯이 존재. 빠른 조치 필요
 - 안정 범위: 항상 0

---

## 운영 가이드 요약
- 지연(latency_ms): 1ms 이상 스파이크 지속 주의. 원인(네트워크/블로킹/GC/디스크)을 빠르게 확인  
- 캐시(hit_rate): 90% 미만 지속 시 TTL/적재/패턴 튜닝  
- 메모리(mem_fragmentation_ratio): 1.4 이상이면 파편화 심각. 재시작/메모리 할당자 튜닝 고려  
- 영속성(AOF/RDB): 쓰기 실패/스냅샷 지연은 디스크/구성 점검  
- 네트워크 버퍼: 증가 추세는 지연 신호. 소비자/네트워크 병목 확인  
- 클러스터 상태: fail/슬롯 실패 발생 시 즉시 원인 분석 및 복구


