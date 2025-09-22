import os

class Config:
    """Application configuration."""
    
    # Read from env var, fallback to a default
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "cool-benefit-472616-t9")
    DATASET_NAME = os.getenv("DATASET_NAME", "usda_dataset")
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")




