import argparse
import json
import sys
import time
from pathlib import Path

import yaml
from tabulate import tabulate

from redis.collector import RedisMetricsCollector
from linux.collector import LinuxMetricsCollector
from kafka.collector import KafkaMetricsCollector
from jvm.collector import JvmMetricsCollector


def load_config(args) -> dict:
	config = {}
	if args.config:
		with open(args.config, "r", encoding="utf-8") as f:
			config = yaml.safe_load(f) or {}
	# CLI가 우선
	if args.redis_url:
		config["redis_url"] = args.redis_url
	if args.interval is not None:
		config["interval"] = args.interval
	if args.output:
		config["output"] = args.output
	if args.ping_samples is not None:
		config["ping_samples"] = args.ping_samples
	if args.ping_timeout_ms is not None:
		config["ping_timeout_ms"] = args.ping_timeout_ms
	# 기본값
	config.setdefault("redis_url", "redis://localhost:6379/0")
	config.setdefault("interval", 0)
	config.setdefault("output", "pretty")
	config.setdefault("ping_samples", 3)
	config.setdefault("ping_timeout_ms", 500)
	return config


def print_output(metrics: dict, output: str):
	if output == "json":
		print(json.dumps(metrics, ensure_ascii=False, indent=2))
		return
	# pretty
	sections = []
	def sec(title: str, items: dict):
		rows = [(k, items.get(k)) for k in items.keys()]
		sections.append(f"[{title}]")
		sections.append(tabulate(rows, headers=["metric", "value"], tablefmt="github"))
		sections.append("")
	# 섹션별 출력
	sec("PERFORMANCE", metrics["performance"])
	sec("MEMORY", metrics["memory"])
	sec("PERSISTENCE", metrics["persistence"])
	sec("NETWORK", metrics["network"])
	sec("SYSTEM", metrics["system"])
	sec("CLUSTER/FAILURE", metrics["cluster"])
	print("\n".join(sections))


def main():
	parser = argparse.ArgumentParser(description="System Monitoring CLI")
	parser.add_argument("--config", type=str, help="설정 파일 경로 (YAML)")
	parser.add_argument("--target", type=str, choices=["redis", "linux", "kafka", "jvm"], default="redis", help="모니터링 대상")
	parser.add_argument("--redis-url", type=str, help="Redis URL, 예: redis://localhost:6379/0")
	parser.add_argument("--kafka-bootstrap", type=str, help="Kafka bootstrap servers, 예: localhost:9092")
	parser.add_argument("--kafka-group", type=str, help="Kafka consumer group(선택, 제공 시 그룹 랙 추정)")
	parser.add_argument("--interval", type=int, help="수집 주기(초). 0이면 1회 수집")
	parser.add_argument("--output", type=str, choices=["pretty", "json"], help="출력 형식")
	parser.add_argument("--ping-samples", type=int, help="핑 지연 샘플 수 (redis)")
	parser.add_argument("--ping-timeout-ms", type=int, help="핑 타임아웃(ms) (redis)")
	args = parser.parse_args()

	config = load_config(args)
	target = args.target or "redis"
	if target == "redis":
		collector = RedisMetricsCollector(
			redis_url=config["redis_url"],
			ping_samples=config["ping_samples"],
			ping_timeout_ms=config["ping_timeout_ms"],
		)
	elif target == "linux":
		collector = LinuxMetricsCollector()
	elif target == "kafka":
		collector = KafkaMetricsCollector(
			bootstrap_servers=args.kafka_bootstrap,
			group_id=args.kafka_group,
		)
	elif target == "jvm":
		collector = JvmMetricsCollector()
	else:
		raise ValueError(f"unknown target: {target}")

	interval = int(config["interval"])
	while True:
		try:
			metrics = collector.collect_all()
			print_output(metrics, config["output"])
		except Exception as e:
			print(f"[ERROR] {e}", file=sys.stderr)
		if interval <= 0:
			break
		time.sleep(interval)


if __name__ == "__main__":
	main()


