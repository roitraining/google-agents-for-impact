# config.py
import os

class Config:
    PROJECT_ID = os.getenv("PROJECT_ID", "cool-benefit-472616-t9")
    LOCATION = os.getenv("LOCATION", "us-central1")

    # Need to create a GCS bucket that images will be uploaded to when users submit them via the web app    
    UPLOAD_BUCKET = os.getenv("UPLOAD_BUCKET", "diet-navigator-uploads-cool-benefit-472616-t9") 
    
    # This will need to be updated with your actual agent engine full address
    Agent_Engine_Full_Adress = os.getenv("Agent_Engine_Full_Adress", "projects/cool-benefit-472616-t9/locations/us-central1/reasoningEngines/6627156802838462464")
    
    
    # Add other Flask config settings if needed
    DEBUG = True
