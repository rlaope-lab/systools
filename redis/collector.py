import json
import time
from typing import Any, Dict, Tuple

import redis


class RedisMetricsCollector:
	def __init__(self, redis_url: str, ping_samples: int = 3, ping_timeout_ms: int = 500):
		self.redis_url = redis_url
		self.ping_samples = max(1, int(ping_samples))
		self.ping_timeout_ms = max(1, int(ping_timeout_ms))
		self.client = redis.from_url(redis_url, decode_responses=True, socket_timeout=ping_timeout_ms / 1000.0)

	def _safe_get(self, dct: Dict[str, Any], key: str, default=None):
		try:
			return dct.get(key, default)
		except Exception:
			return default

	def _measure_latency_ms(self) -> float:
		# 간단한 라운드트립 PING으로 지연 측정 (샘플 평균)
		samples = []
		for _ in range(self.ping_samples):
			start = time.perf_counter()
			self.client.ping()
			elapsed_ms = (time.perf_counter() - start) * 1000.0
			samples.append(elapsed_ms)
		return sum(samples) / len(samples)

	def _parse_client_buffers(self) -> Tuple[int, int]:
		# CLIENT LIST를 파싱해 input/output buffer 추정 합계 계산
		total_input = 0
		total_output = 0
		try:
			raw = self.client.execute_command("CLIENT", "LIST")
			# redis-py decode_responses=True → 문자열
			for line in raw.splitlines():
				# 필드는 key=value 형식
				fields = {}
				for part in line.split(" "):
					if "=" in part:
						k, v = part.split("=", 1)
						fields[k] = v
				# 버전에 따라 다름: qbuf(입력 대기), qbuf-free, obl/omem/obuf(출력)
				# 가능한 필드를 최대한 합산
				# 입력 추정
				for k in ("qbuf", "ibl", "input_buffer_length"):
					if k in fields:
						try:
							total_input += int(fields[k])
						except Exception:
							pass
				# 출력 추정
				for k in ("obuf", "omem", "obl", "output_buffer_length"):
					if k in fields:
						try:
							total_output += int(fields[k])
						except Exception:
							pass
		except Exception:
			# 일부 버전/권한에서 실패 가능
			pass
		return total_input, total_output

	def _cluster_slots_stats(self) -> Tuple[int, int, int]:
		# cluster_slots_assigned, cluster_slots_pfail, cluster_slots_fail
		# CLUSTER SLOTS로 계산: assigned는 총 할당된 슬롯 수, pfail/fail은 CLUSTER NODES 기반이 일반적이나
		# 간단화: SLOTS 출력 범위로 assigned 계산, pfail/fail은 CLUSTER INFO가 직접 제공하지 않아 0으로 처리
		try:
			slots = self.client.execute_command("CLUSTER", "SLOTS")
			assigned = 0
			for slot in slots:
				start, end = slot[0], slot[1]
				assigned += (end - start + 1)
			# pfail/fail은 CLUSTER NODES 파싱이 필요하나 간단 구현에서는 0
			return assigned, 0, 0
		except Exception:
			return 0, 0, 0

	def collect_all(self) -> Dict[str, Dict[str, Any]]:
		info_all = self.client.info()
		server_now = int(time.time())
		latency_ms = self._measure_latency_ms()
		total_input_buf, total_output_buf = self._parse_client_buffers()

		# 성능
		perf = {
			"instantaneous_ops_per_sec": self._safe_get(info_all, "instantaneous_ops_per_sec"),
			"latency_ms": round(latency_ms, 3),
			"total_commands_processed": self._safe_get(info_all, "total_commands_processed"),
			"keyspace_hits": self._safe_get(info_all, "keyspace_hits"),
			"keyspace_misses": self._safe_get(info_all, "keyspace_misses"),
			"hit_rate": None,
			"expired_keys": self._safe_get(info_all, "expired_keys"),
		}
		hits = perf["keyspace_hits"] or 0
		misses = perf["keyspace_misses"] or 0
		try:
			perf["hit_rate"] = round(hits / (hits + misses), 6) if (hits + misses) > 0 else None
		except Exception:
			perf["hit_rate"] = None

		# 메모리
		mem = {
			"used_memory": self._safe_get(info_all, "used_memory"),
			"used_memory_rss": self._safe_get(info_all, "used_memory_rss"),
			"used_memory_peak": self._safe_get(info_all, "used_memory_peak"),
			"mem_fragmentation_ratio": self._safe_get(info_all, "mem_fragmentation_ratio"),
			"maxmemory": self._safe_get(info_all, "maxmemory"),
			"evicted_keys": self._safe_get(info_all, "evicted_keys"),
			"allocator_stats": None,
		}
		# jemalloc allocator stats (있을 경우)
		try:
			mem_stats_raw = self.client.execute_command("MEMORY", "MALLOC-STATS")
			mem["allocator_stats"] = mem_stats_raw
		except Exception:
			mem["allocator_stats"] = None

		# 영속성
		persist = {
			"rdb_last_save_time": self._safe_get(info_all, "rdb_last_save_time"),
			"rdb_changes_since_last_save": self._safe_get(info_all, "rdb_changes_since_last_save"),
			"aof_current_size": self._safe_get(info_all, "aof_current_size"),
			"aof_base_size": self._safe_get(info_all, "aof_base_size"),
			"aof_last_write_status": self._safe_get(info_all, "aof_last_write_status"),
		}

		# 네트워크
		network = {
			"connected_clients": self._safe_get(info_all, "connected_clients"),
			"blocked_clients": self._safe_get(info_all, "blocked_clients"),
			"input_buffer_length": total_input_buf if total_input_buf > 0 else None,
			"output_buffer_length": total_output_buf if total_output_buf > 0 else None,
		}

		# 시스템/CPU
		system = {
			"used_cpu_sys": self._safe_get(info_all, "used_cpu_sys"),
			"used_cpu_user": self._safe_get(info_all, "used_cpu_user"),
			"used_cpu_sys_children": self._safe_get(info_all, "used_cpu_sys_children"),
			"used_cpu_user_children": self._safe_get(info_all, "used_cpu_user_children"),
		}

		# 복제/클러스터
		cluster = {
			"master_link_status": None,
			"master_last_io_seconds_ago": None,
			"repl_backlog_size": self._safe_get(info_all, "repl_backlog_size"),
			"cluster_state": None,
			"cluster_slots_assigned": None,
			"cluster_slots_pfail": None,
			"cluster_slots_fail": None,
		}
		# 복제 (replication)
		try:
			rep = self.client.info("replication")
			cluster["master_link_status"] = rep.get("master_link_status")
			cluster["master_last_io_seconds_ago"] = rep.get("master_last_io_seconds_ago")
			if cluster["repl_backlog_size"] is None:
				cluster["repl_backlog_size"] = rep.get("repl_backlog_size")
		except Exception:
			pass
		# 클러스터
		try:
			cinfo = self.client.execute_command("CLUSTER", "INFO")
			# 문자열 포맷을 파싱
			state_map = {}
			for line in cinfo.splitlines():
				if ":" in line:
					k, v = line.split(":", 1)
					state_map[k.strip()] = v.strip()
			cluster["cluster_state"] = state_map.get("cluster_state")
		except Exception:
			cluster["cluster_state"] = None
		assigned, pfail, fail = self._cluster_slots_stats()
		cluster["cluster_slots_assigned"] = assigned
		cluster["cluster_slots_pfail"] = pfail
		cluster["cluster_slots_fail"] = fail

		return {
			"performance": perf,
			"memory": mem,
			"persistence": persist,
			"network": network,
			"system": system,
			"cluster": cluster,
			"meta": {
				"timestamp": server_now,
				"redis_url": self.redis_url,
			},
		}


