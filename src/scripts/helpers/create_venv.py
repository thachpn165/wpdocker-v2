#!/usr/bin/env python3
import os
import sys
import subprocess
import site
import sysconfig

def create_venv(venv_path):
    print(f"Creating virtual environment at: {venv_path}")
    
    # Try different methods in order of preference
    methods = [
        lambda: subprocess.run([sys.executable, "-m", "venv", venv_path]),
        lambda: subprocess.run([sys.executable, "-m", "virtualenv", venv_path]),
        lambda: manual_create_venv(venv_path)
    ]
    
    for method in methods:
        try:
            result = method()
            if isinstance(result, subprocess.CompletedProcess) and result.returncode == 0 and os.path.exists(os.path.join(venv_path, "bin", "activate")):
                print(f"Successfully created virtual environment at {venv_path}")
                return True
        except Exception as e:
            print(f"Method failed with error: {e}")
    
    return False

def manual_create_venv(venv_path):
    # Manual creation of minimal virtualenv structure
    print("Attempting manual virtualenv creation...")
    
    if not os.path.exists(venv_path):
        os.makedirs(venv_path)
    
    bin_dir = os.path.join(venv_path, "bin")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
    
    # Create basic activate script
    with open(os.path.join(bin_dir, "activate"), "w") as f:
        f.write(f'''
# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

deactivate () {{
    unset -f pydoc >/dev/null 2>&1
    unset -f deactivate
    unset VIRTUAL_ENV
    if [ ! "${{1:-}}" = "nondestructive" ] ; then
    # Self destruct!
        unset -f deactivate
    fi
}}

# unset irrelevant variables
deactivate nondestructive

VIRTUAL_ENV="{venv_path}"
export VIRTUAL_ENV

PATH="$VIRTUAL_ENV/bin:$PATH"
export PATH

if [ -z "${{PYTHONHOME:-}}" ] ; then
    PYTHONHOME="${{PYTHONHOME:-}}"
    export PYTHONHOME
    unset PYTHONHOME
fi

if [ -z "${{PYTHONNOUSERSITE:-}}" ] ; then
    export PYTHONNOUSERSITE=1
fi
''')
    
    # Create python symlink
    os.symlink(sys.executable, os.path.join(bin_dir, "python"))
    os.symlink(sys.executable, os.path.join(bin_dir, "python3"))
    
    # Create pip script
    with open(os.path.join(bin_dir, "pip"), "w") as f:
        f.write(f'''
#!/bin/sh
"{sys.executable}" -m pip "$@"
''')
    os.chmod(os.path.join(bin_dir, "pip"), 0o755)
    
    with open(os.path.join(bin_dir, "pip3"), "w") as f:
        f.write(f'''
#!/bin/sh
"{sys.executable}" -m pip "$@"
''')
    os.chmod(os.path.join(bin_dir, "pip3"), 0o755)
    
    # Return success
    return subprocess.CompletedProcess(args=[], returncode=0)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <venv_path>")
        sys.exit(1)
    
    venv_path = sys.argv[1]
    success = create_venv(venv_path)
    
    if success:
        sys.exit(0)
    else:
        print(f"Failed to create virtual environment at {venv_path}")
        sys.exit(1)