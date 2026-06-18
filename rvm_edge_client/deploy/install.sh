#!/bin/bash
# EcoPoints Deployment Installer for Raspberry Pi 5

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

# Detect current directory (assuming this script is inside /deploy)
DEPLOY_DIR=$(pwd)
WORKDIR=$(dirname "$DEPLOY_DIR")
# Get the non-root user who invoked sudo (usually 'pi' or your custom username)
ACTUAL_USER=${SUDO_USER:-pi}
USER_HOME=$(eval echo ~$ACTUAL_USER)

echo "Installing EcoPoints services for user '$ACTUAL_USER' at '$WORKDIR'..."

# Process templates and copy to systemd directory
for service in ecopoints-backend.service ecopoints-frontend.service ecopoints-kiosk.service; do
    echo "Configuring $service..."
    sed -e "s|__WORKDIR__|$WORKDIR|g" \
        -e "s|User=pi|User=$ACTUAL_USER|g" \
        -e "s|/home/pi|$USER_HOME|g" \
        $service > /etc/systemd/system/$service
done

echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling services to start on boot..."
systemctl enable ecopoints-backend.service
systemctl enable ecopoints-frontend.service
systemctl enable ecopoints-kiosk.service

echo "Starting services now..."
systemctl restart ecopoints-backend.service
systemctl restart ecopoints-frontend.service
systemctl restart ecopoints-kiosk.service

echo "========================================="
echo "Installation Complete!"
echo "Your Raspberry Pi will now automatically launch EcoPoints on every boot."
echo "To check the status of the backend, run:  systemctl status ecopoints-backend.service"
echo "To view backend logs, run:                journalctl -u ecopoints-backend.service -f"
echo "========================================="
