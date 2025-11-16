import os
import shutil
from typing import Dict, Any, Tuple, List
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

	def _read_proc_stat_cpu(self) -> Tuple[int, int]:
		# returns (idle, total) jiffies
		try:
			with open("/proc/stat", "r", encoding="utf-8") as f:
				line = f.readline()
				if not line.startswith("cpu "):
					return 0, 0
				parts = line.strip().split()
				values = list(map(int, parts[1:]))  # user nice system idle iowait irq softirq steal guest guest_nice
				idle = values[3] + (values[4] if len(values) > 4 else 0)
				total = sum(values)
				return idle, total
		except Exception:
			return 0, 0

	def _cpu_usage_percent(self, sample_ms: int = 200) -> float | None:
		idle1, total1 = self._read_proc_stat_cpu()
		if total1 == 0:
			return None
		time.sleep(max(sample_ms, 1) / 1000.0)
		idle2, total2 = self._read_proc_stat_cpu()
		delta_total = total2 - total1
		delta_idle = idle2 - idle1
		if delta_total <= 0:
			return None
		usage = 100.0 * (delta_total - delta_idle) / delta_total
		return round(usage, 2)

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

	def _read_net_dev_per_iface(self) -> Dict[str, Dict[str, int]]:
		stats: Dict[str, Dict[str, int]] = {}
		try:
			with open("/proc/net/dev", "r", encoding="utf-8") as f:
				for line in f:
					if ":" not in line:
						continue
					iface, data = line.split(":", 1)
					iface = iface.strip()
					fields = data.split()
					if len(fields) >= 16:
						stats[iface] = {
							"rx_bytes": int(fields[0]),
							"rx_packets": int(fields[1]),
							"tx_bytes": int(fields[8]),
							"tx_packets": int(fields[9]),
						}
		except Exception:
			pass
		return stats

	def _list_mountpoints(self) -> List[Tuple[str, str]]:
		mounts: List[Tuple[str, str]] = []
		try:
			with open("/proc/mounts", "r", encoding="utf-8") as f:
				for line in f:
					parts = line.split()
					if len(parts) < 3:
						continue
					device, mnt, fstype = parts[0], parts[1], parts[2]
					# 물리 볼륨 위주 필터
					if fstype in ("ext2", "ext3", "ext4", "xfs", "btrfs", "zfs"):
						mounts.append((mnt, fstype))
		except Exception:
			pass
		# 루트는 항상 포함
		if ("/", "unknown") not in mounts and not any(m == "/" for m, _ in mounts):
			mounts.append(("/", "unknown"))
		# 중복 제거
		seen = set()
		unique: List[Tuple[str, str]] = []
		for m, t in mounts:
			if m in seen:
				continue
			seen.add(m)
			unique.append((m, t))
		return unique

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
		mem_used_kb = None
		mem_used_percent = None
		swap_used_kb = None
		swap_used_percent = None
		try:
			if mem_total_kb is not None and mem_available_kb is not None:
				mem_used_kb = max(mem_total_kb - mem_available_kb, 0)
				mem_used_percent = round(100.0 * mem_used_kb / mem_total_kb, 2) if mem_total_kb > 0 else None
			if swap_total_kb is not None and swap_free_kb is not None:
				swap_used_kb = max(swap_total_kb - swap_free_kb, 0)
				swap_used_percent = round(100.0 * swap_used_kb / swap_total_kb, 2) if swap_total_kb > 0 else None
		except Exception:
			pass

		# 디스크(root)
		per_mount: Dict[str, Dict[str, int | float | None]] = {}
		try:
			for mount, fstype in self._list_mountpoints():
				try:
					du = shutil.disk_usage(mount)
					used_percent = round(100.0 * du.used / du.total, 2) if du.total > 0 else None
					per_mount[mount] = {
						"fstype": fstype,
						"total_bytes": du.total,
						"used_bytes": du.used,
						"free_bytes": du.free,
						"used_percent": used_percent,
					}
				except Exception:
					continue
		except Exception:
			pass

		# 네트워크 총계
		rx_bytes, tx_bytes = self._read_net_dev_bytes()
		per_iface = self._read_net_dev_per_iface()

		# 기타
		uptime_seconds = self._read_uptime()
		cpu_count = os.cpu_count()
		cpu_usage_percent = self._cpu_usage_percent()

		# 프로세스 수
		process_count = None
		try:
			process_count = sum(1 for name in os.listdir("/proc") if name.isdigit())
		except Exception:
			pass

		# 파일 디스크립터
		fd_allocated = fd_max = None
		try:
			with open("/proc/sys/fs/file-nr", "r", encoding="utf-8") as f:
				parts = f.read().split()
				# file-nr: allocated unused max
				if len(parts) >= 3:
					fd_allocated = int(parts[0])
					fd_max = int(parts[2])
		except Exception:
			pass

		return {
			"system": {
				"uptime_seconds": uptime_seconds,
				"cpu_count": cpu_count,
				"loadavg_1": load1,
				"loadavg_5": load5,
				"loadavg_15": load15,
				"cpu_usage_percent": cpu_usage_percent,
				"process_count": process_count,
			},
			"memory": {
				"mem_total_kb": mem_total_kb,
				"mem_available_kb": mem_available_kb,
				"mem_used_kb": mem_used_kb,
				"mem_used_percent": mem_used_percent,
				"swap_total_kb": swap_total_kb,
				"swap_free_kb": swap_free_kb,
				"swap_used_kb": swap_used_kb,
				"swap_used_percent": swap_used_percent,
			},
			"disk": per_mount,
			"network": {
				"rx_bytes_total": rx_bytes,
				"tx_bytes_total": tx_bytes,
				"interfaces": per_iface,
			},
			"fs": {
				"fd_allocated": fd_allocated,
				"fd_max": fd_max,
			},
			"meta": {
				"timestamp": int(time.time()),
				"node": os.uname().nodename if hasattr(os, "uname") else None,
				"kernel": " ".join(os.uname()) if hasattr(os, "uname") else None,
			},
		}


