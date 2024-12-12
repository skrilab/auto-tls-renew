import os
import requests
import paramiko
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from telegram import send_notification

# Load environment variables from .env file
load_dotenv()

API_URL = os.getenv("API_URL")
API_TOKEN_URL = f"{API_URL}/tokens"
CERTIFICATES_URL = f"{API_URL}/nginx/certificates"
MIKROTIK_HOST = os.getenv("MIKROTIK_HOST")
MIKROTIK_USER = os.getenv("MIKROTIK_USER")
MIKROTIK_PASSWORD = os.getenv("MIKROTIK_PASSWORD")
INTERFACE = os.getenv("MIKROTIK_INTERFACE")
RULE_IDS = os.getenv("MIKROTIK_RULE_ID")

# Function to get access token for Nginx Proxy Manager
def get_token():
    """Request a new access token."""
    response = requests.post(API_TOKEN_URL, json={
        "identity": os.getenv("API_IDENTITY"),
        "secret": os.getenv("API_SECRET"),
        "scope": "user"
    })
    response.raise_for_status()
    return response.json()["token"]

# Function to list all TLS certificates
def get_certificates(token):
    """Fetch certificates information."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(CERTIFICATES_URL, headers=headers)
    response.raise_for_status()
    return response.json()

# Function to renew TLS certificates
def renew_certificate(token, cert_id):
    """Renew a specific certificate."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{CERTIFICATES_URL}/{cert_id}/renew", headers=headers)
    response.raise_for_status()
    return response.json()

# Function to connect to Mikrotik
def connect_mikrotik():
    """Connect to MikroTik router using SSH."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(MIKROTIK_HOST, username=MIKROTIK_USER, password=MIKROTIK_PASSWORD)
    return client

# Function to check Public (it's dynamic) IP on Mikrotik
def get_ip_address(client, INTERFACE):
    """Get the IP address assigned to a specified interface."""
    command = f"/ip address print detail where interface={INTERFACE}"
    stdin, stdout, stderr = client.exec_command(command)
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if error:
        print("Error fetching IP address:", error)
        return None
    
    # Parse the output to find the IP address
    for line in output.splitlines():
        if "address=" in line:
            # Extract the IP address
            ip_address = line.split("address=")[1].split()[0]
            ip_address = ip_address.split('/')[0]
            print(ip_address)
            return ip_address
    
    print("No IP address found on interface", INTERFACE)
    return None

# Function to update NAT rule with Public IP
def update_nat_rule_dst_address(client, RULE_IDS, ip_address):
    """Update the destination address of a NAT rule."""
    command = f'/ip firewall nat set numbers={RULE_IDS} dst-address={ip_address}'
    stdin, stdout, stderr = client.exec_command(command)
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if error:
        print("Error updating NAT rule:", error)
    else:
        print("NAT rule updated successfully!")

# Function to enable NAT rule on Mikrotik
def enable_nat_rule(client, RULE_IDS):
    """Enable NAT rule on MikroTik."""
    command = f'/ip firewall nat enable numbers={RULE_IDS}'
    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read().decode()
    error = stderr.read().decode()

    if error:
        print("Error enabling NAT rule:", error)
    else:
        print("NAT rule enabled successfully!")

# Function to disable NAT rule on Mikrotik
def disable_nat_rule(client, RULE_IDS):
    """Disable NAT rule on MikroTik."""
    command = f'/ip firewall nat disable numbers={RULE_IDS}'
    stdin, stdout, stderr = client.exec_command(command)
    print(stdout.read().decode())
    print(stderr.read().decode())


def main():
    # Get the access token
    token = get_token()
    
    # Fetch the certificates
    certificates = get_certificates(token)

    # Prepare Mikrotik for TLS cert update
    client = connect_mikrotik()          
    ip_address = get_ip_address(client, INTERFACE)          
    update_nat_rule_dst_address(client, RULE_IDS, ip_address)
    enable_nat_rule(client, RULE_IDS)

    # Process each certificate in the list
    for cert in certificates:
        # Parse the expiration date from the certificate
        expiry_date = datetime.strptime(cert["expires_on"], '%Y-%m-%d %H:%M:%S')

        # Print the expiration date for debugging
        print(f"Certificate ID: {cert['id']}, Expires On: {expiry_date}")

        # Check if the certificate is expiring within the next 15 days
        if expiry_date < datetime.now() + timedelta(days=15):
            print(f"Renewing certificate: {cert['id']}, Domain Name: {cert['domain_names']}")
            time.sleep(5)

            # Renew the certificate
            renew_certificate(token, cert['id'])

            time.sleep(20)
            
    disable_nat_rule(client, RULE_IDS)
    client.close()

if __name__ == "__main__":
    main()

# Uncomment the function you want to test run
#   token = get_token()
#   print("Token:", token)
#   client = connect_mikrotik()
#   ip_address = get_ip_address(client, INTERFACE)