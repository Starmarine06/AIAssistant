import os
import sys
import shutil
import subprocess
from PIL import Image, ImageDraw

def generate_ico_file(output_path):
    """Generate a sleek, professional Windows .ico file with multiple sizes."""
    print("Generating professional app icon...")
    
    # Standard sizes for Windows ICO
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Create an image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Scale parameters based on size
        margin = max(1, size // 16)
        width_outer = max(1, size // 30)
        
        # Draw a beautiful dark-blue circular background with white border
        draw.ellipse(
            [margin, margin, size - margin, size - margin], 
            fill=(30, 144, 255, 255), 
            outline=(255, 255, 255, 255), 
            width=width_outer
        )
        
        # Draw stylized 'A' in the center
        left_foot = (int(size * 0.35), int(size * 0.70))
        right_foot = (int(size * 0.65), int(size * 0.70))
        apex = (int(size * 0.50), int(size * 0.28))
        
        line_w1 = max(2, int(size * 0.08))
        line_w2 = max(1, int(size * 0.06))
        
        # Left leg
        draw.line([left_foot[0], left_foot[1], apex[0], apex[1]], fill=(255, 255, 255, 255), width=line_w1)
        # Right leg
        draw.line([right_foot[0], right_foot[1], apex[0], apex[1]], fill=(255, 255, 255, 255), width=line_w1)
        # Crossbar
        cross_left = (int(size * 0.41), int(size * 0.56))
        cross_right = (int(size * 0.59), int(size * 0.56))
        draw.line([cross_left[0], cross_left[1], cross_right[0], cross_right[1]], fill=(255, 255, 255, 255), width=line_w2)
        
        images.append(img)
        
    # Save as multi-size ICO
    images[0].save(output_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f"Icon saved to: {output_path}")

def clean_build_files():
    """Clean up build and spec files."""
    print("Cleaning temporary build files...")
    dirs_to_remove = ["build"]
    files_to_remove = ["bot.spec", "AIAssistant_Setup.spec"]
    
    for d in dirs_to_remove:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except Exception as e:
                print(f"Warning: could not delete directory {d}: {e}")
                
    for f in files_to_remove:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception as e:
                print(f"Warning: could not delete file {f}: {e}")

def run_command(command_list):
    """Run system command and print output."""
    cmd_str = " ".join(command_list)
    print(f"Running command: {cmd_str}")
    process = subprocess.Popen(
        command_list, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, 
        shell=True,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Print stdout in real-time
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            
    rc = process.poll()
    if rc != 0:
        raise subprocess.CalledProcessError(rc, command_list)

def build():
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(workspace_dir)
    
    # 1. Generate app icon
    icon_path = "app_icon.ico"
    generate_ico_file(icon_path)
    
    # 2. Build bot.exe
    print("\nPhase 1: Compiling bot.py to standalone executable...")
    bot_build_cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--icon={icon_path}",
        "--collect-all", "customtkinter",
        "--name=bot",
        "bot.py"
    ]
    try:
        run_command(bot_build_cmd)
        print("Phase 1 complete: bot.exe created!")
    except Exception as e:
        print(f"Error building bot.exe: {e}")
        sys.exit(1)
        
    # Verify bot.exe exists before proceeding
    built_bot_path = os.path.join("dist", "bot.exe")
    if not os.path.exists(built_bot_path):
        print("Error: bot.exe was not found in the dist folder after compilation!")
        sys.exit(1)

    # 3. Build AIAssistant_Setup.exe
    print("\nPhase 2: Compiling installer.py and bundling bot.exe...")
    add_data_flag = f"{built_bot_path};."
    
    installer_build_cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        f"--icon={icon_path}",
        "--collect-all", "customtkinter",
        "--add-data", add_data_flag,
        "--name=AIAssistant_Setup",
        "installer.py"
    ]
    try:
        run_command(installer_build_cmd)
        print("Phase 2 complete: AIAssistant_Setup.exe created!")
    except Exception as e:
        print(f"Error building installer setup: {e}")
        sys.exit(1)

    # 4. Copy finals to workspace root for convenience
    print("\nMoving final build outputs to workspace root...")
    try:
        if os.path.exists("bot.exe"):
            os.remove("bot.exe")
        if os.path.exists("AIAssistant_Setup.exe"):
            os.remove("AIAssistant_Setup.exe")
            
        shutil.copy2(os.path.join("dist", "bot.exe"), "bot.exe")
        shutil.copy2(os.path.join("dist", "AIAssistant_Setup.exe"), "AIAssistant_Setup.exe")
        print("Executables copied to workspace root successfully!")
    except Exception as e:
        print(f"Warning: Could not copy executables to workspace root: {e}")

    # 5. Clean up build files
    clean_build_files()
    
    print("\nBUILD COMPLETE SUCCESS!")
    print("--------------------------------------------------")
    print("Final Deliverables:")
    print("1. Standalone Bot EXE: bot.exe")
    print("2. Setup Installer EXE: AIAssistant_Setup.exe")
    print("--------------------------------------------------")

if __name__ == "__main__":
    build()
