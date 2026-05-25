# BenchAnything Environments

Smoke-test repository for SWECC Mesocosm / BenchAnything environments.

The current root environment is `Tic Tac Toe Smoke Test`. It is intentionally
root-level because the remote benchmarker clones the submitted GitHub repo and
expects `benchanything.json` at the repository root.

## Local Smoke Test

```bash
python3 adapter.py --host 127.0.0.1 --port 8765
```

Then, in another terminal:

```bash
curl -s http://127.0.0.1:8765/health

curl -s -X POST http://127.0.0.1:8765/reset \
  -H "Content-Type: application/json" \
  -d '{"episode_id":"smoke-1","seed":42}' | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8765/step \
  -H "Content-Type: application/json" \
  -d '{"episode_id":"smoke-1","action":"4"}' | python3 -m json.tool

curl -s -X POST http://127.0.0.1:8765/close \
  -H "Content-Type: application/json" \
  -d '{"episode_id":"smoke-1"}'
```

## Remote Submit

Once pushed to GitHub as a public repo, submit:

```bash
curl -X POST https://api.swecc.org/bench/v1/developer/environments \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "FWT-bs",
    "name": "Tic Tac Toe Smoke Test",
    "github_url": "https://github.com/FWT-bs/environments",
    "description": "A compact tic-tac-toe benchmark where the agent plays X against a seeded novice O opponent."
  }'
```

You can also use the web form at:

https://swecc-uw.github.io/swecc-mesocosm/#/developer
