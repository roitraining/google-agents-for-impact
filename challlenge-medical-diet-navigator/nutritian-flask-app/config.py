# config.py
import os

class Config:
    PROJECT_ID = os.getenv("PROJECT_ID", "cool-benefit-472616-t9")
    LOCATION = os.getenv("LOCATION", "us-central1")
    SERVICE_ACCOUNT_EMAIL = os.getenv("SERVICE_ACCOUNT_EMAIL", "278550033422-compute@developer.gserviceaccount.com")
   
    # Add other Flask config settings if needed
    DEBUG = True
