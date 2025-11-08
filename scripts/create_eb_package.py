#!/usr/bin/env python3
"""
Create Elastic Beanstalk deployment package with proper timestamps
"""
import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

def fix_zip_timestamps(source_dir, output_file):
    """Create ZIP file with all timestamps >= 1980-01-01"""
    min_date = datetime(1980, 1, 1)
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Skip directories we don't want
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git']]
            
            for file in files:
                # Skip files we don't want
                if file.startswith('.') or file.endswith('.pyc'):
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                
                # Get file info
                stat = os.stat(file_path)
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                # Ensure timestamp is >= 1980-01-01
                if mtime < min_date:
                    mtime = min_date
                
                # Add to zip with fixed timestamp
                zip_info = zipfile.ZipInfo(arcname, mtime.timetuple()[:6])
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                
                with open(file_path, 'rb') as f:
                    zipf.writestr(zip_info, f.read())
    
    print(f"Created deployment package: {output_file}")

if __name__ == "__main__":
    # Create temp directory with only files we need
    temp_dir = "eb_deploy_temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Copy necessary files (excluding what's in .ebignore)
    exclude_patterns = [
        '__pycache__', '.git', '.vscode', '.idea', 'node_modules',
        'frontend', 'docs', 'scripts', 'aws', 'tests', 'data/raw', 'data/processed',
        '.pytest_cache', 'venv', 'env', 'ENV', '*.pyc', '.env'
    ]
    
    # Copy files
    for root, dirs, files in os.walk('.'):
        # Filter directories
        dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]
        
        for file in files:
            if any(file.endswith(ext) for ext in ['.pyc', '.log', '.md']) and file != 'README.md':
                continue
                
            src = os.path.join(root, file)
            rel_path = os.path.relpath(src, '.')
            dst = os.path.join(temp_dir, rel_path)
            
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    
    # Create ZIP
    output_file = "spendsenseai-deploy.zip"
    fix_zip_timestamps(temp_dir, output_file)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print(f"Deployment package ready: {output_file}")
    print("You can upload this to Elastic Beanstalk manually or use: eb deploy --source codebundle")




