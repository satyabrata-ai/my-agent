# app/config.py
"""
Central configuration management for the agent.
Loads settings from environment variables and .env file.
"""

import os
from pathlib import Path
from typing import Optional

# Try to load python-dotenv if available
try:
    from dotenv import load_dotenv
    # Load .env from project root
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    print(f"✓ Loaded configuration from {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables only.")
    print("   Install with: pip install python-dotenv")


class Config:
    """Application configuration loaded from environment variables"""
    
    # Google Cloud Settings
    GOOGLE_CLOUD_PROJECT: str = os.getenv(
        "GOOGLE_CLOUD_PROJECT", 
        "ccibt-hack25ww7-706"
    )
    GOOGLE_CLOUD_LOCATION: str = os.getenv(
        "GOOGLE_CLOUD_LOCATION", 
        "global"
    )
    GOOGLE_GENAI_USE_VERTEXAI: str = os.getenv(
        "GOOGLE_GENAI_USE_VERTEXAI", 
        "True"
    )
    LOGS_BUCKET_NAME: str = os.getenv(
        "LOGS_BUCKET_NAME", 
        "gs://ccibt-agent-logs"
    )
    
    # GCS Data Bucket Settings
    GCS_DATA_BUCKET: str = os.getenv(
        "GCS_DATA_BUCKET",
        "gs://datasets-ccibt-hack25ww7-706"  # Default to known bucket
    )
    GCS_DATASET_PREFIX: str = os.getenv(
        "GCS_DATASET_PREFIX",
        "datasets/uc4-market-activity-prediction-agent"
    )
    
    # Agent Memory Settings
    GCS_MEMORY_PATH: str = os.getenv(
        "GCS_MEMORY_PATH",
        "agent_memory"  # Path within GCS bucket for persistent memory
    )
    
    # Model Configuration
    AGENT_MODEL: str = os.getenv(
        "AGENT_MODEL",
        "gemini-2.5-flash"  # Default model
        # "gemini-3-pro-preview"
    )
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Computed properties
    @property
    def dataset_path(self) -> str:
        """Full path to datasets in GCS"""
        if not self.GCS_DATA_BUCKET:
            raise ValueError(
                "GCS_DATA_BUCKET not set. Please configure it in .env file"
            )
        return f"{self.GCS_DATA_BUCKET}/{self.GCS_DATASET_PREFIX}"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"
    
    def get_dataset_file_path(self, filename: str) -> str:
        """
        Get full GCS path for a dataset file
        
        Args:
            filename: Name of the dataset file
            
        Returns:
            Full GCS path (e.g., gs://bucket/datasets/prefix/filename)
        """
        return f"{self.dataset_path}/{filename}"
    
    def validate(self) -> bool:
        """
        Validate that all required configuration is set
        
        Returns:
            True if valid, raises ValueError if not
        """
        if not self.GCS_DATA_BUCKET or self.GCS_DATA_BUCKET == "":
            print("⚠️  GCS_DATA_BUCKET not set - memory will not persist!")
            print("   Set GCS_DATA_BUCKET in .env file for persistence")
        
        if not self.GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT is required")
        
        return True
    
    def __repr__(self) -> str:
        """String representation (hides sensitive data)"""
        return (
            f"Config(\n"
            f"  environment={self.ENVIRONMENT}\n"
            f"  project={self.GOOGLE_CLOUD_PROJECT}\n"
            f"  location={self.GOOGLE_CLOUD_LOCATION}\n"
            f"  model={self.AGENT_MODEL}\n"
            f"  data_bucket={self.GCS_DATA_BUCKET}\n"
            f"  dataset_prefix={self.GCS_DATASET_PREFIX}\n"
            f")"
        )


# Create singleton instance
config = Config()

# Validate on import (warnings only - won't fail deployment)
try:
    config.validate()
    print(f"✓ Configuration validated successfully")
    print(f"   Model: {config.AGENT_MODEL}")
    print(f"   Environment: {config.ENVIRONMENT}")
except ValueError as e:
    print(f"⚠️  Configuration warning: {e}")
    print(f"   Continuing with available configuration...")


# Export for easy imports
__all__ = ['config', 'Config']