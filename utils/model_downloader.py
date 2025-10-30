"""
Model Downloader Utility
Checks for local model and downloads if not present
"""

import os
import subprocess
import sys
from pathlib import Path


def check_and_download_model(
    model_name: str = "sentence-transformers/static-retrieval-mrl-en-v1",
    local_dir: str = "./models"
) -> str:
    """
    Check if model exists locally, download if not.
    
    Args:
        model_name: Hugging Face model identifier (e.g., "sentence-transformers/static-retrieval-mrl-en-v1")
        local_dir: Directory to store models
        
    Returns:
        str: Path to model (either Hugging Face identifier or local path)
    """
    # Extract model folder name from full identifier
    model_folder_name = model_name.split('/')[-1]
    model_path = os.path.join(local_dir, model_folder_name)
    
    # Check if model already exists locally
    if os.path.exists(model_path) and os.path.isdir(model_path):
        # Verify it has required files
        required_files = ['config.json', 'pytorch_model.bin']
        has_required_files = any(
            os.path.exists(os.path.join(model_path, f)) 
            for f in required_files
        )
        
        if has_required_files:
            print(f"✓ Model found locally: {model_path}")
            return model_path
        else:
            print(f"⚠ Model folder exists but incomplete: {model_path}")
            print(f"  Will attempt to download...")
    else:
        print(f"Model not found locally: {model_path}")
        print(f"Attempting to download...")
    
    # Create models directory if it doesn't exist
    os.makedirs(local_dir, exist_ok=True)
    
    # Try multiple download methods
    success = False
    
    # Method 1: Try huggingface-cli (preferred)
    if not success:
        success = download_with_hf_cli(model_name, model_path)
    
    # Method 2: Try git clone (fallback)
    if not success:
        success = download_with_git(model_name, model_path)
    
    # Method 3: Try downloading with Python (last resort)
    if not success:
        success = download_with_python(model_name, model_path)
    
    if success:
        print(f"✓ Model downloaded successfully to: {model_path}")
        return model_path
    else:
        print(f"✗ Could not download model. Using Hugging Face Hub (requires internet).")
        return model_name  # Return original name to download on-the-fly


def download_with_hf_cli(model_name: str, local_path: str) -> bool:
    """
    Download model using Hugging Face CLI.
    
    Args:
        model_name: Model identifier
        local_path: Local destination path
        
    Returns:
        bool: True if successful
    """
    print("Attempting download with huggingface-cli...")
    
    try:
        # Check if huggingface-cli is installed
        result = subprocess.run(
            ['huggingface-cli', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("  huggingface-cli not installed")
            return False
        
        print(f"  Found huggingface-cli: {result.stdout.strip()}")
        
        # Download model
        print(f"  Downloading {model_name}...")
        download_result = subprocess.run(
            [
                'huggingface-cli',
                'download',
                model_name,
                '--local-dir', local_path,
                '--local-dir-use-symlinks', 'False'
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if download_result.returncode == 0:
            print("  ✓ Download successful with huggingface-cli")
            return True
        else:
            print(f"  ✗ Download failed: {download_result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ✗ Download timed out")
        return False
    except FileNotFoundError:
        print("  huggingface-cli not found in PATH")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def download_with_git(model_name: str, local_path: str) -> bool:
    """
    Download model using git clone.
    
    Args:
        model_name: Model identifier
        local_path: Local destination path
        
    Returns:
        bool: True if successful
    """
    print("Attempting download with git clone...")
    
    try:
        # Check if git is installed
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("  git not installed")
            return False
        
        print(f"  Found git: {result.stdout.strip()}")
        
        # Construct Hugging Face repo URL
        repo_url = f"https://huggingface.co/{model_name}"
        
        print(f"  Cloning from {repo_url}...")
        
        # Remove directory if it exists but is empty/incomplete
        if os.path.exists(local_path):
            import shutil
            shutil.rmtree(local_path)
        
        # Clone repository
        clone_result = subprocess.run(
            ['git', 'clone', repo_url, local_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if clone_result.returncode == 0:
            print("  ✓ Clone successful with git")
            return True
        else:
            print(f"  ✗ Clone failed: {clone_result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ✗ Clone timed out")
        return False
    except FileNotFoundError:
        print("  git not found in PATH")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def download_with_python(model_name: str, local_path: str) -> bool:
    """
    Download model using Python huggingface_hub library.
    
    Args:
        model_name: Model identifier
        local_path: Local destination path
        
    Returns:
        bool: True if successful
    """
    print("Attempting download with huggingface_hub Python library...")
    
    try:
        from huggingface_hub import snapshot_download
        
        print(f"  Downloading {model_name}...")
        
        snapshot_download(
            repo_id=model_name,
            local_dir=local_path,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        print("  ✓ Download successful with huggingface_hub")
        return True
        
    except ImportError:
        print("  huggingface_hub not installed")
        print("  Install with: pip install huggingface-hub")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def install_huggingface_cli():
    """
    Install huggingface-cli if not present.
    """
    print("\nInstalling huggingface-hub (includes CLI)...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade', 'huggingface-hub'
        ])
        print("✓ huggingface-hub installed successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to install huggingface-hub: {e}")
        return False
