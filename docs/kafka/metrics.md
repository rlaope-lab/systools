# Kafka 모니터링 지표(초안)

본 모듈은 `kafka-python`을 이용해 경량 메트릭을 수집합니다.

## 수집 항목
- broker
  - num_brokers: 메타데이터 상 브로커 수(추정)
- topics
  - num_topics: 토픽 수
  - num_partitions: 전체 파티션 수 합
- lag (옵션)
  - consumer_group_id: CLI로 전달된 그룹 ID
  - consumer_lag_total: 각 파티션의 end_offset - committed_offset 합(음수는 0 처리)
- meta
  - timestamp, bootstrap_servers

주의
- 그룹 랙 계산은 `--kafka-group` 제공 시에만 작동합니다.
- 브로커 수/메타데이터는 클라이언트 내부 메타데이터 기반이므로 일시적으로 부정확할 수 있습니다.
- Throughput(초당 in/out 바이트)은 브로커 JMX/관리 API 연동 시 확장 예정입니다.

## 실행 예시
```bash
# 토픽/파티션/브로커 수만
python monitor.py --target kafka --kafka-bootstrap localhost:9092 --output json

# 그룹 랙 포함
python monitor.py --target kafka --kafka-bootstrap localhost:9092 --kafka-group my-consumer --output json
```

