This script automates the Nginx Proxy Manager TLS certificate renewal process for a locked homelab (the lab is accessible only locally) environment with a Mikrotik router. The status messages of the renewal process is sent to a Telegram bot.

Still, in my case, due to a dynamic public IP, the public DNS records update part is a manual process (this is because of missing automation options in the selected/used DNS registrar).

### Setup
0. Modify the .env file
1. Install Python requirements
```
pip install -r requirements.txt
```
2. Schedule the script to run every day or so

### ToDo
-  Create a function that checks if public DNS records need to be updated to align with Mikrotik's public IP.

