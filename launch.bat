@echo off
echo Creating virtual environment...
python -m venv venv

echo Activating environment and installing dependencies...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo Starting the app...
streamlit run app.py

pause
