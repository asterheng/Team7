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
