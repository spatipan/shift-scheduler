from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError

from source import *
from Interface_demo import GoogleSheetApp, SchedulerApp

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/solve")
async def solve():
    schedulerApp = SchedulerApp()
    schedulerApp.solve()
    return {"message": "Solved"}
