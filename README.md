## Como rodar

python -m venv .venv
# Windows
. .venv/Scripts/activate
pip install fastapi uvicorn sqlalchemy

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

