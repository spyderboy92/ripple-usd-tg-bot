#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Update the package list and install system dependencies
echo "Updating system packages..."
sudo yum update -y
sudo yum install -y git python3 python3-pip

# Set Python3 as default python
sudo alternatives --install /usr/bin/python python /usr/bin/python3 1
sudo alternatives --set python /usr/bin/python3

# Clone the repository
echo "Cloning the repository..."
git clone https://github.com/spyderboy92/ripple-usd-tg-bot.git
cd ripple-usd-tg-bot

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set PYTHONPATH and run the bot
echo "Starting the bot..."
export PYTHONPATH=$(pwd)
export BOT_API_KEY=CHANGE_THIS
nohup python tg/bot.py &

echo "Bot is running in the background."
