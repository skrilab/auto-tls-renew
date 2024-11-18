import os
import requests
import paramiko
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

API_URL = os.getenv("API_URL")
API_TOKEN_URL = f"{API_URL}/tokens"
CERTIFICATES_URL = f"{API_URL}/nginx/certificates"
RENEW_CERTIFICATE_URL = f"{API_URL}/nginx/certificates/renew"
MIKROTIK_HOST = os.getenv("MIKROTIK_HOST")
MIKROTIK_USER = os.getenv("MIKROTIK_USER")
MIKROTIK_PASSWORD = os.getenv("MIKROTIK_PASSWORD")
interface = os.getenv("MIKROTIK_INTERFACE")  # Load interface from .env
rule_id = os.getenv("MIKROTIK_RULE_ID")  # Load rule ID from .env


def get_token():
    """Request a new access token."""
    response = requests.post(API_TOKEN_URL, json={
        "identity": os.getenv("API_IDENTITY"),
        "secret": os.getenv("API_SECRET"),
        "scope": "user"
    })
    response.raise_for_status()
    return response.json()["token"]

def get_certificates(token):
    """Fetch certificates information."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(CERTIFICATES_URL, headers=headers)
    response.raise_for_status()
    return response.json()

def renew_certificate(token, cert_id):
    """Renew a specific certificate."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{RENEW_CERTIFICATE_URL}/{cert_id}", headers=headers)
    response.raise_for_status()
    return response.json()

def connect_mikrotik():
    """Connect to MikroTik router using SSH."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(MIKROTIK_HOST, username=MIKROTIK_USER, password=MIKROTIK_PASSWORD)
    return client

def get_ip_address(client, interface):
    """Get the IP address assigned to a specified interface."""
    command = f"/ip address print detail where interface={interface}"
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
    
    print("No IP address found on interface", interface)
    return None

def update_nat_rule_dst_address(client, rule_id, ip_address):
    """Update the destination address of a NAT rule."""
    command = f'/ip firewall nat set numbers={rule_id} dst-address={ip_address}'
    stdin, stdout, stderr = client.exec_command(command)
    
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if error:
        print("Error updating NAT rule:", error)
    else:
        print("NAT rule updated successfully!")

def enable_nat_rule(client, rule_id):
    """Enable NAT rule on MikroTik."""
    command = f'/ip firewall nat enable numbers={rule_id}'
    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read().decode()
    error = stderr.read().decode()

    if error:
        print("Error enabling NAT rule:", error)
    else:
        print("NAT rule enabled successfully!")

def disable_nat_rule(client, rule_id):
    """Disable NAT rule on MikroTik."""
    command = f'/ip firewall nat disable numbers={rule_id}'
    stdin, stdout, stderr = client.exec_command(command)
    print(stdout.read().decode())
    print(stderr.read().decode())

def main():
    token = get_token()
    certificates = get_certificates(token)

    for cert in certificates.get("data", []):
        expiry_date = datetime.fromtimestamp(cert["expires"])
        if expiry_date < datetime.now() + timedelta(days=30):  # Check if expiring in 30 days
            print(f"Renewing certificate: {cert['id']}")
            enable_nat_rule(connect_mikrotik())
            renew_certificate(token, cert["id"])
            disable_nat_rule(connect_mikrotik())

if __name__ == "__main__":
    #main()

# Uncomment the function you want to run
    #token = get_token()
    #print("Token:", token)

    # Uncomment to get certificates
    #certificates = get_certificates(token)
    #print("Certificates:", certificates)

    # Uncomment to renew a certificate (provide a valid cert_id)
    # result = renew_certificate(token, "your_certificate_id")
    # print("Renewed Certificate:", result)

    # Uncomment to enable NAT rule
    client = connect_mikrotik()
    
    ip_address = get_ip_address(client, interface)
    
    update_nat_rule_dst_address(client, rule_id, ip_address)
    enable_nat_rule(client, rule_id)
    #disable_nat_rule(client, rule_id)
    client.close()
