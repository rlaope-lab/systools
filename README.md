# systools

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
# redis
python monitor.py --target redis --redis-url redis://localhost:6379/0 --interval 5 --output pretty

# linux
python monitor.py --target linux --interval 5 --output json
```

- `--target`: redis | linux | kafka | jvm
- `--redis-url`: Redis 연결 URL (예: `redis://:password@host:6379/0`)
- `--interval`: 수집 주기(초), 0이면 1회만 수집
- `--output`: pretty | json

use config:
```bash
python monitor.py --target redis --config config.yaml
```
