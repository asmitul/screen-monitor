# 1 . create .env variable

# 2 . local dev : 
## in Windows
```bash
pip install virtualenv
virtualenv --python python\path venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe

## in Linux
```bash
python3 -m venv venv
pip install -r requirements.txt
```

# convert to exe
```bash
pip install pyinstaller
pyinstaller --onefile main.py
```