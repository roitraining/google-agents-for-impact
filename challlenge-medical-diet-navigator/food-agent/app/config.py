import os

class Config:
    """Application configuration."""
    
    # Read from env var, fallback to a default
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "cool-benefit-472616-t9")
    DATASET_NAME = os.getenv("DATASET_NAME", "usda_dataset")
    MODEL = os.getenv("MODEL", "gemini-2.5-flash")

    # Need to create a bucket in your project. (It must be public)
    # Image generation will write images to this bucket.
    IMAGE_BUCKET = os.getenv("IMAGE_BUCKET", "food-agent-generated-images-dar")
                               
    




