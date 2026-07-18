#!/bin/bash
set -e

echo "=== AI Assistant Linux Installer ==="

# 1. Install system dependencies if apt is available
if [ -x "$(command -v apt-get)" ]; then
    echo "Installing system dependencies via apt..."
    sudo apt-get update
    sudo apt-get install -y xclip xdotool scrot python3-tk python3-pip python3-venv plocate fd-find grim gnome-screenshot
else
    echo "Warning: Package manager 'apt-get' not found."
    echo "Please ensure xclip, xdotool, scrot, python3-tk, plocate, fd, grim, and gnome-screenshot are installed on your system."
fi

# 2. Setup python virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create launching script
echo "Creating run script..."
cat << 'EOF' > run_bot.sh
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
source venv/bin/activate
python bot.py
EOF
chmod +x run_bot.sh

# 4. Create Desktop Entry
echo "Creating desktop shortcut..."
DESKTOP_DIR="$HOME/Desktop"
APP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

mkdir -p "$APP_DIR"
mkdir -p "$AUTOSTART_DIR"

# Generate desktop file content
cat << EOF > AIAssistant.desktop
[Desktop Entry]
Type=Application
Name=AI Assistant
Comment=AI Assistant Telegram Bot & Controller
Exec=$(pwd)/run_bot.sh
Icon=$(pwd)/app_icon.ico
Terminal=false
Categories=Utility;
EOF
chmod +x AIAssistant.desktop

# Copy to applications list
cp AIAssistant.desktop "$APP_DIR/"

# Copy to Desktop if directory exists
if [ -d "$DESKTOP_DIR" ]; then
    cp AIAssistant.desktop "$DESKTOP_DIR/"
fi

# Copy to Autostart (Startup)
cp AIAssistant.desktop "$AUTOSTART_DIR/"

echo "=== Installation Complete! ==="
echo "Shortcuts have been created on your Desktop, Applications menu, and Autostart folder."
echo "You can run the bot by executing: ./run_bot.sh"
