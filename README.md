# install deps
pip install -r requirements.txt

# create the SQLite DB (optional if your app creates it automatically)
# from repo root:
mkdir -p instance
sqlite3 instance/team7.db ".databases" ".quit"

# run app
python run.py
