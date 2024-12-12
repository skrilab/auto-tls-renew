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


# Get access token for Nginx Proxy Manager
def get_token():
    response = requests.post(API_TOKEN_URL, json={
        "identity": os.getenv("API_IDENTITY"),
        "secret": os.getenv("API_SECRET"),
        "scope": "user"
    })
    response.raise_for_status()
    return response.json()["token"]


# List all TLS certificates
def get_certificates(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(CERTIFICATES_URL, headers=headers)
    response.raise_for_status()
    return response.json()

# Renew TLS certificates
def renew_certificate(token, cert_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{CERTIFICATES_URL}/{cert_id}/renew", headers=headers)
    
    # Check if the response was successful
    try:
        response.raise_for_status()  # Raise an error for bad responses
        result = response.json()  # Parse the JSON response
        
        # Send the success notification
        send_notification(f"TLS certificate for {result['domain_names']} renewed successfully on {result['modified_on']}!")
        
        return result  # Return the result if needed
    
    except requests.exceptions.HTTPError as err:
        # Send an error notification
        send_notification(f"Failed to renew certificate {cert_id}: {err}")
        raise  # Re-raise the error after sending notification


# Connect to Mikrotik with ssh
def connect_mikrotik():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(MIKROTIK_HOST, username=MIKROTIK_USER, password=MIKROTIK_PASSWORD)
    return client


# Check Public (it's dynamic) IP on Mikrotik
def get_ip_address(client, INTERFACE):
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


# Update NAT rule with Public IP
def update_nat_rule_dst_address(client, RULE_IDS, ip_address):
    command = f'/ip firewall nat set numbers={RULE_IDS} dst-address={ip_address}'
    stdin, stdout, stderr = client.exec_command(command)
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if error:
        print("Error updating NAT rule:", error)
    else:
        print("NAT rule updated successfully!")


# Enable NAT rule on Mikrotik
def enable_nat_rule(client, RULE_IDS):
    command = f'/ip firewall nat enable numbers={RULE_IDS}'
    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read().decode()
    error = stderr.read().decode()

    if error:
        print("Error enabling NAT rule:", error)
    else:
        print("NAT rule enabled successfully!")


# Disable NAT rule on Mikrotik
def disable_nat_rule(client, RULE_IDS):
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
        expiry_date = datetime.strptime(cert['expires_on'], '%Y-%m-%d %H:%M:%S')

        # Check if the certificate is expiring within the next 15 days
        if expiry_date < datetime.now() + timedelta(days=68):
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