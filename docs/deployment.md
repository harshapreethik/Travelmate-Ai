# TravelMate AI — Production Deployment Guide

This guide provides the full set of production launch commands across **Windows**, **Linux**, and **macOS**.

---

## 1. Windows Deployment (Waitress)

Activate your virtual environment, install Waitress, and launch the WSGI production server:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install waitress
waitress-serve --port=5000 app:app

2. Linux Deployment (Gunicorn)
Activate your environment, install Gunicorn, and start the multi-process server:

source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

3. macOS Deployment (Gunicorn / Waitress)
Activate your environment and launch using Gunicorn or Waitress:

source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
gunicorn -w 2 -b 127.0.0.1:5000 app:app