import time
from typing import Any, Dict


class JvmMetricsCollector:
	def __init__(self, jmx_url: str | None = None):
		# 실제 구현은 JMX 연동(jolokia/pyjmx 등)을 통해 값 채움
		self.jmx_url = jmx_url

	def collect_all(self) -> Dict[str, Dict[str, Any]]:
		# 24개 대표 메트릭 필드(기본 None) - 구조 확정
		memory = {
			"heap_used_bytes": None,              # 1
			"heap_committed_bytes": None,         # 2
			"heap_max_bytes": None,               # 3
			"non_heap_used_bytes": None,          # 4
			"non_heap_committed_bytes": None,     # 5
			"metaspace_used_bytes": None,         # 6
			"metaspace_committed_bytes": None,    # 7
		}
		gc = {
			"young_gc_count": None,               # 8
			"young_gc_time_ms": None,             # 9
			"old_gc_count": None,                 # 10
			"old_gc_time_ms": None,               # 11
		}
		threads = {
			"thread_count": None,                 # 12
			"daemon_thread_count": None,          # 13
			"peak_thread_count": None,            # 14
			"deadlocked_thread_count": None,      # 15
		}
		classloading = {
			"loaded_class_count": None,           # 16
			"total_loaded_class_count": None,     # 17
			"unloaded_class_count": None,         # 18
		}
		cpu = {
			"process_cpu_load": None,             # 19
			"system_cpu_load": None,              # 20
			"process_cpu_time_ns": None,          # 21
		}
		runtime = {
			"uptime_ms": None,                    # 22
			"compiler_total_time_ms": None,       # 23
			"safepoint_count": None,              # 24
		}
		return {
			"memory": memory,
			"gc": gc,
			"threads": threads,
			"classloading": classloading,
			"cpu": cpu,
			"runtime": runtime,
			"meta": {
				"timestamp": int(time.time()),
				"jmx_url": self.jmx_url,
				"not_implemented": True,
			},
		}


