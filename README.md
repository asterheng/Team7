# Team7

pip install flask flask_sqlalchemy werkzeug

python run.py

//db (https://www.sqlite.org/download.html) -> install sqlite3 ->edit variable to run in CLI cd -> Team7 -> instance -> sqlite3 team7.db



flowchart LR
  A["Developer commits"] --> B["GitHub Action builds/tests"]
  B --> C["Pull Request and Merge"]
  C --> D["Deployment (localhost)"]
