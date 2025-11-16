from flask import Flask, render_template, request
import os
import time

from redis.collector import RedisMetricsCollector
from linux.collector import LinuxMetricsCollector
from kafka.collector import KafkaMetricsCollector
from jvm.collector import JvmMetricsCollector

app = Flask(__name__, template_folder="templates", static_folder="static")


def collect_safe(collector_name: str, fn):
	try:
		return {"name": collector_name, "data": fn(), "error": None}
	except Exception as e:
		return {"name": collector_name, "data": None, "error": str(e)}


@app.route("/")
def index():
	targets = request.args.get("targets", "redis,linux,kafka,jvm")
	target_list = [t.strip() for t in targets.split(",") if t.strip()]

	results = []
	now = int(time.time())

	if "redis" in target_list:
		redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
		ping_samples = int(os.environ.get("REDIS_PING_SAMPLES", "3"))
		ping_timeout_ms = int(os.environ.get("REDIS_PING_TIMEOUT_MS", "500"))
		rc = RedisMetricsCollector(redis_url, ping_samples, ping_timeout_ms)
		results.append(collect_safe("redis", rc.collect_all))

	if "linux" in target_list:
		lc = LinuxMetricsCollector()
		results.append(collect_safe("linux", lc.collect_all))

	if "kafka" in target_list:
		bootstrap = os.environ.get("KAFKA_BOOTSTRAP")
		group_id = os.environ.get("KAFKA_GROUP")
		kc = KafkaMetricsCollector(bootstrap_servers=bootstrap, group_id=group_id)
		results.append(collect_safe("kafka", kc.collect_all))

	if "jvm" in target_list:
		jmx_url = os.environ.get("JMX_URL")
		jc = JvmMetricsCollector(jmx_url=jmx_url)
		results.append(collect_safe("jvm", jc.collect_all))

	return render_template("index.html", results=results, ts=now)


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


