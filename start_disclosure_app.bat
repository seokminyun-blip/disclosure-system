@echo off
cd /d "c:\Users\윤석민\OneDrive - (주)니어스랩\바탕 화면\VS code\OPEN"
start "" /B .venv\Scripts\streamlit.exe run disclosure_system\app.py --server.address 0.0.0.0 --server.port 8501
