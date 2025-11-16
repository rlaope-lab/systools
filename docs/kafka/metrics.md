# Kafka 모니터링 지표(스켈레톤)

현재는 구조만 제공됩니다. 실제 연결/수집은 향후 `kafka-python` 또는 관리 API/JMX 연동으로 추가됩니다.

- broker: cluster_id, num_brokers, controller_id
- topics: num_topics, num_partitions
- throughput: bytes_in_per_sec, bytes_out_per_sec
- lag: consumer_lag_total

요청 시 Brokers/JMX 연결 방식과 인증 옵션을 설계하여 구현을 진행합니다.

