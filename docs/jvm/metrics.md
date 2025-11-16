# JVM 모니터링 지표(24선, 구조 확정)

현재 문서는 JVM 메트릭 24개 항목의 구조/의미를 정의합니다. 실제 값은 추후 JMX 연동(jolokia/pyjmx 등)으로 채웁니다.

## Memory
1) heap_used_bytes  
2) heap_committed_bytes  
3) heap_max_bytes  
4) non_heap_used_bytes  
5) non_heap_committed_bytes  
6) metaspace_used_bytes  
7) metaspace_committed_bytes  
- 의미: JVM 메모리 사용/커밋/최대, 메타스페이스 사용량

## GC
8) young_gc_count  
9) young_gc_time_ms  
10) old_gc_count  
11) old_gc_time_ms  
- 의미: Young/Old(G1/Parallel/CMS 등) 컬렉션 횟수/시간

## Threads
12) thread_count  
13) daemon_thread_count  
14) peak_thread_count  
15) deadlocked_thread_count  
- 의미: 스레드 수/피크/교착상태 스레드 수

## ClassLoading
16) loaded_class_count  
17) total_loaded_class_count  
18) unloaded_class_count  
- 의미: 클래스 로딩/언로딩 통계

## CPU
19) process_cpu_load  
20) system_cpu_load  
21) process_cpu_time_ns  
- 의미: 프로세스/시스템 CPU 부하 및 프로세스 CPU 누적 시간

## Runtime
22) uptime_ms  
23) compiler_total_time_ms  
24) safepoint_count  
- 의미: JVM 업타임, JIT 컴파일 누적, 세이프포인트 진입 횟수

주의
- HotSpot 기반 MXBean/JFR/Jolokia에서 제공되는 표준/벤더 지표를 우선 사용합니다.
- 실제 수집은 JMX URL, 인증, SSL 등 연결 설정이 필요합니다.

