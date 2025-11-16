# JVM 모니터링 지표(스켈레톤)

현재는 구조만 제공되며, 실제 수집은 JMX 연동(jolokia/pyjmx 등)을 통해 추가 예정입니다.

- memory: heap_used_bytes, heap_max_bytes, non_heap_used_bytes
- gc: gc_count, gc_time_ms
- threads: thread_count, daemon_thread_count

요청 시 JMX 접근 방식(보안/SSL/자격증명 포함)을 정의하고 구현합니다.

