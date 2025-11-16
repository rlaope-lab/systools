# Redis Monitoring (핵심 33선 지표 수집기)

이 도구는 Redis의 핵심 성능/메모리/영속성/네트워크/CPU/클러스터 지표 33선을 수집·표시합니다.  
CLI로 즉시 사용하거나 주기적으로 출력할 수 있습니다.

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 빠른 시작

```bash
python monitor.py --redis-url redis://localhost:6379 --interval 5 --output pretty
```

- `--redis-url`: Redis 연결 URL (예: `redis://:password@host:6379/0`)
- `--interval`: 수집 주기(초), 0이면 1회만 수집
- `--output`: pretty | json

## 설정 파일 사용

`config.yaml` 예시 파일이 제공됩니다.

```bash
python monitor.py --config config.yaml
```

CLI 옵션이 설정 파일을 덮어씁니다.

## 수집 지표

- 성능: instantaneous_ops_per_sec, latency_ms(핑 기반), total_commands_processed, keyspace_hits, keyspace_misses, hit_rate, expired_keys
- 메모리: used_memory, used_memory_rss, used_memory_peak, mem_fragmentation_ratio, maxmemory, evicted_keys, allocator_stats(jemalloc)
- 영속성: rdb_last_save_time, rdb_changes_since_last_save, aof_current_size, aof_base_size, aof_last_write_status
- 네트워크: connected_clients, blocked_clients, input_buffer_length(bytes, 추정), output_buffer_length(bytes, 추정)
- CPU/시스템: used_cpu_sys, used_cpu_user, used_cpu_sys_children, used_cpu_user_children
- 클러스터/장애: master_link_status, master_last_io_seconds_ago, repl_backlog_size, cluster_state, cluster_slots_assigned, cluster_slots_pfail, cluster_slots_fail

일부 필드는 Redis 버전/빌드 옵션에 따라 미보고될 수 있습니다(예: allocator_stats).

## 주의

- `latency_ms`는 `PING` 라운드트립 기반으로 추정합니다(간단·가벼움).
- `input/output_buffer_length`는 `CLIENT LIST`를 통해 추정 합계를 계산합니다(필드명은 버전에 따라 차이).


