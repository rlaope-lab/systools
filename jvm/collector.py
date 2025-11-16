import time
from typing import Any, Dict


class JvmMetricsCollector:
	def __init__(self, jmx_url: str | None = None):
		# 실제 구현은 JMX 접속 라이브러리 필요(jolokia/pyjmx 등)
		self.jmx_url = jmx_url

	def collect_all(self) -> Dict[str, Dict[str, Any]]:
		# 스켈레톤: 구조만 반환
		return {
			"memory": {
				"heap_used_bytes": None,
				"heap_max_bytes": None,
				"non_heap_used_bytes": None,
			},
			"gc": {
				"gc_count": None,
				"gc_time_ms": None,
			},
			"threads": {
				"thread_count": None,
				"daemon_thread_count": None,
			},
			"meta": {
				"timestamp": int(time.time()),
				"jmx_url": self.jmx_url,
				"not_implemented": True,
			},
		}


