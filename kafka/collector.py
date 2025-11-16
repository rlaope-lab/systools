import time
from typing import Any, Dict, List

try:
	from kafka import KafkaConsumer, TopicPartition
	from kafka.errors import KafkaError
except Exception:  # pragma: no cover
	KafkaConsumer = None
	TopicPartition = None
	KafkaError = Exception


class KafkaMetricsCollector:
	def __init__(self, bootstrap_servers: str | None = None, group_id: str | None = None, timeout_ms: int = 3000):
		self.bootstrap_servers = bootstrap_servers
		self.group_id = group_id
		self.timeout_ms = timeout_ms

	def _build_consumer(self) -> KafkaConsumer | None:
		if KafkaConsumer is None or not self.bootstrap_servers:
			return None
		try:
			consumer = KafkaConsumer(
				bootstrap_servers=self.bootstrap_servers,
				group_id=self.group_id if self.group_id else None,
				client_id="systools-kafka",
				enable_auto_commit=False,
				consumer_timeout_ms=self.timeout_ms,
				request_timeout_ms=max(self.timeout_ms, 5000),
				metadata_max_age_ms=5000,
				api_version_auto_timeout_ms=3000,
			)
			return consumer
		except Exception:
			return None

	def _compute_topics_partitions(self, consumer: KafkaConsumer) -> Dict[str, int]:
		num_topics = 0
		num_partitions = 0
		try:
			topics = consumer.topics()
			num_topics = len(topics or [])
			for t in topics or []:
				parts = consumer.partitions_for_topic(t)
				if parts:
					num_partitions += len(parts)
		except Exception:
			pass
		return {"num_topics": num_topics, "num_partitions": num_partitions}

	def _num_brokers(self, consumer: KafkaConsumer) -> int | None:
		try:
			cluster = consumer._client.cluster  # 내부 속성 사용(없으면 None)
			if cluster:
				return len(cluster.brokers())
		except Exception:
			return None
		return None

	def _group_lag(self, consumer: KafkaConsumer) -> int | None:
		if not self.group_id:
			return None
		try:
			topics = list(consumer.topics() or [])
			tps: List[TopicPartition] = []
			for t in topics:
				parts = consumer.partitions_for_topic(t) or []
				for p in parts:
					tps.append(TopicPartition(t, p))
			if not tps:
				return 0
			end_offsets = consumer.end_offsets(tps)
			total_lag = 0
			for tp in tps:
				committed = consumer.committed(tp)
				end = end_offsets.get(tp, None)
				if committed is None or end is None:
					continue
				lag = max(end - committed, 0)
				total_lag += lag
			return total_lag
		except Exception:
			return None

	def collect_all(self) -> Dict[str, Dict[str, Any]]:
		consumer = self._build_consumer()

		num_brokers = None
		topics_info = {"num_topics": None, "num_partitions": None}
		group_lag_total = None

		if consumer:
			num_brokers = self._num_brokers(consumer)
			topics_info = self._compute_topics_partitions(consumer)
			group_lag_total = self._group_lag(consumer)
			try:
				consumer.close()
			except Exception:
				pass

		return {
			"broker": {
				"num_brokers": num_brokers,
			},
			"topics": topics_info,
			"lag": {
				"consumer_group_id": self.group_id,
				"consumer_lag_total": group_lag_total,
			},
			"meta": {
				"timestamp": int(time.time()),
				"bootstrap_servers": self.bootstrap_servers,
			},
		}


