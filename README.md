# 1 . create .env variable

# 2 . local dev : 
## in Windows
```bash
pip install virtualenv
virtualenv --python python\path venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## in Linux
```bash
python3 -m venv venv
pip install -r requirements.txt
```

```bash
pyinstaller --onefile main.py
```