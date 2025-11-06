# install deps
pip install -r requirements.txt

# create the SQLite DB (optional if your app creates it automatically)
# from repo root:
mkdir -p instance
sqlite3 instance/team7.db ".databases" ".quit"

# run app
python run.py


## CI/CD Flow

```mermaid
flowchart LR
  A["Developer commits"] --> B["GitHub Action builds/tests"]
  B --> C["Pull Request and Merge"]
  C --> D["Deployment (localhost)"]

## Evidence Summary

| Evidence | Description |
|-----------|--------------|
| ✅ CI Run | GitHub Actions shows “Build successful” on push |
| 🔄 Integration Flow | Mermaid CI/CD flow diagram renders correctly |
| 🏷️ Release | Final demo build published as v1.0 |
