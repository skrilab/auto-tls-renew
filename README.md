This script automates the Nginx Proxy Manager TLS certificate renewal process for locked (the lab is accessible only locally) homelab environments with a Mikrotik router.

Still, in my case, due to a dynamic public IP, the public DNS records update part is a manual process (this is because of missing automation options in the selected/used DNS registrar).

### Setup
1. Install Python requirements
```
pip install -r requirements.txt
```
2. Schedule the script to run every day or so

### ToDo
-  Implement some kind of notifications (Gotify or Telegram) to phone/PC about successful/error events.
-  Create a function that checks if public DNS records need to be updated to align with Mikrotik's public IP.