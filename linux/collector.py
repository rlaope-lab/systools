import os
import shutil
from typing import Dict, Any, Tuple
import time


class LinuxMetricsCollector:
	def __init__(self):
		if os.name != "posix":
			# 리눅스 전용(일부 macOS에서도 동작하지만 /proc 의존 기능은 제한)
			pass

	def _read_proc_meminfo(self) -> Dict[str, int]:
		result: Dict[str, int] = {}
		try:
			with open("/proc/meminfo", "r", encoding="utf-8") as f:
				for line in f:
					parts = line.split(":")
					if len(parts) < 2:
						continue
					key = parts[0].strip()
					value_part = parts[1].strip().split()[0]
					try:
						result[key] = int(value_part)  # kB 단위
					except Exception:
						continue
		except Exception:
			pass
		return result

	def _read_uptime(self) -> float:
		try:
			with open("/proc/uptime", "r", encoding="utf-8") as f:
				return float(f.read().split()[0])
		except Exception:
			return 0.0

	def _read_net_dev_bytes(self) -> Tuple[int, int]:
		rx = 0
		tx = 0
		try:
			with open("/proc/net/dev", "r", encoding="utf-8") as f:
				for line in f:
					if ":" not in line:
						continue
					iface, data = line.split(":", 1)
					fields = data.split()
					if len(fields) >= 16:
						rx += int(fields[0])
						tx += int(fields[8])
		except Exception:
			pass
		return rx, tx

	def collect_all(self) -> Dict[str, Dict[str, Any]]:
		# 로드 평균
		try:
			load1, load5, load15 = os.getloadavg()
		except Exception:
			load1 = load5 = load15 = None

		# 메모리
		meminfo = self._read_proc_meminfo()
		mem_total_kb = meminfo.get("MemTotal")
		mem_available_kb = meminfo.get("MemAvailable")
		swap_total_kb = meminfo.get("SwapTotal")
		swap_free_kb = meminfo.get("SwapFree")

		# 디스크(root)
		try:
			du = shutil.disk_usage("/")
			disk_total = du.total
			disk_used = du.used
			disk_free = du.free
		except Exception:
			disk_total = disk_used = disk_free = None

		# 네트워크 총계
		rx_bytes, tx_bytes = self._read_net_dev_bytes()

		# 기타
		uptime_seconds = self._read_uptime()
		cpu_count = os.cpu_count()

		return {
			"system": {
				"uptime_seconds": uptime_seconds,
				"cpu_count": cpu_count,
				"loadavg_1": load1,
				"loadavg_5": load5,
				"loadavg_15": load15,
			},
			"memory": {
				"mem_total_kb": mem_total_kb,
				"mem_available_kb": mem_available_kb,
				"swap_total_kb": swap_total_kb,
				"swap_free_kb": swap_free_kb,
			},
			"disk": {
				"root_total_bytes": disk_total,
				"root_used_bytes": disk_used,
				"root_free_bytes": disk_free,
			},
			"network": {
				"rx_bytes_total": rx_bytes,
				"tx_bytes_total": tx_bytes,
			},
			"meta": {
				"timestamp": int(time.time()),
				"node": os.uname().nodename if hasattr(os, "uname") else None,
			},
		}


