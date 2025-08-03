#!/usr/bin/env python3
"""
Script to check version consistency across multiple files.
"""
import sys
import re
from pathlib import Path

def get_version_from_file(file_path, pattern):
    """Extract version from a file using a regex pattern."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        return None
    except FileNotFoundError:
        print(f"Warning: {file_path} not found")
        return None

def main():
    """Check version consistency across all relevant files."""
    project_root = Path(__file__).parent.parent
    
    # Define version patterns for different files
    version_files = {
        'pyproject.toml': r'version\s*=\s*["\']([^"\']+)["\']',
        'setup.py': r'version\s*=\s*["\']([^"\']+)["\']',
        'setup.cfg': r'version\s*=\s*([^\s]+)',
        'src/vllm_top/__init__.py': r'__version__\s*=\s*["\']([^"\']+)["\']',
    }
    
    versions = {}
    for file_path, pattern in version_files.items():
        full_path = project_root / file_path
        version = get_version_from_file(full_path, pattern)
        if version:
            versions[file_path] = version
    
    if not versions:
        print("Error: No version information found in any file")
        sys.exit(1)
    
    # Check consistency
    unique_versions = set(versions.values())
    
    if len(unique_versions) == 1:
        version = list(unique_versions)[0]
        print(f"✅ All versions are consistent: {version}")
        
        # Validate version format (semantic versioning)
        if not re.match(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$', version):
            print(f"❌ Version format is invalid: {version}")
            print("Expected format: X.Y.Z or X.Y.Z-suffix")
            sys.exit(1)
            
        sys.exit(0)
    else:
        print("❌ Version inconsistency detected:")
        for file_path, version in versions.items():
            print(f"  {file_path}: {version}")
        sys.exit(1)

if __name__ == '__main__':
    main()
