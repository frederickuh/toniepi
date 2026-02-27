#!/bin/bash

echo "Updating system..."
sudo apt update && sudo apt upgrade -y

echo "Installing system packages..."
sudo apt install -y python3-pip python3-venv mpg123 git

echo "Enabling SPI and I2C..."
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating systemd service..."
sudo cp toniepi.service /etc/systemd/system/toniepi.service
sudo systemctl daemon-reload
sudo systemctl enable toniepi

echo "Creating data folders..."
mkdir -p audio data

echo "Installation complete!"
echo "Rebooting in 5 seconds..."
sleep 5
sudo reboot