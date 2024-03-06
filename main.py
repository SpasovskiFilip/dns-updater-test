"""
DNS Updater
Author: Alexandru-Ioan Plesoiu
GitHub: https://github.com/alexplesoiu
Documentation: https://github.com/alexplesoiu/dns-updater

DNS Updater is a Python-based tool that automatically updates Cloudflare DNS records
with your public IP address. If your server's IP address changes frequently or you
have a dynamic IP, this tool ensures that your domains and subdomains always point
to the correct server. It can handle multiple domains and subdomains from multiple
zones, with proxying enabled or disabled. The tool runs checks and updates every
5 minutes and includes redundancy for IP checking services.
"""

import requests
import schedule
import time
import socket
import logging
import sys
import os
import json

# Replace with your actual data
CF_API_KEY = os.getenv("CF_API_KEY")
CF_EMAIL = os.getenv("CF_EMAIL")
CF_ZONE_ID = os.getenv("CF_ZONE_ID")
DNS_RECORD_COMMENT_KEY = os.getenv('DNS_RECORD_COMMENT_KEY')
DOMAINS_FILE_PATH = os.getenv('DOMAINS_FILE_NAME')
SCHEDULE_MINUTES = os.getenv('SCHEDULE_MINUTES', 60)

# Define API endpoints
BASE_URL = 'https://api.cloudflare.com/client/v4/'

# List of IP checking services
IP_CHECK_SERVICES = [
    'https://adresameaip.ro/ip',
    'https://api.ipify.org',
    'https://icanhazip.com',
    'https://ipinfo.io/ip'
]

def create_logger(level=logging.INFO):
    """ Create the logger object """
    logger = logging.getLogger("MGE-Logs")

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler('dns_updater.log')

    console_handler.setLevel(level)
    file_handler.setLevel(logging.WARNING)

    # Create formatters and add it :w:wto handlers
    logger_format = logging.Formatter('%(asctime)s | %(filename)s | %(levelname)s | %(message)s')
    file_format = logging.Formatter('%(asctime)s | %(filename)s(%(lineno)d) | %(levelname)s | %(message)s')

    file_handler.setFormatter(file_format)
    console_handler.setFormatter(logger_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(level)

    return logger


LOGGER = create_logger()


# Get current DNS record for the specified domain
def get_dns_record(zone_id, domain_name):
    headers = {
        'X-Auth-Email': CF_EMAIL,
        'X-Auth-Key': CF_API_KEY,
        'Content-Type': 'application/json',
    }

    params = {
        'name': domain_name,
    }

    response = requests.get(f'{BASE_URL}zones/{zone_id}/dns_records', headers=headers, params=params)

    if response.status_code == 200:
        records = response.json()['result']
        if records:
            return records[0]
    return None


# Get current DNS records that contain a key inside of comment
def get_dns_records_by_comment(zone_id, comment_key):
    headers = {
        'X-Auth-Email': CF_EMAIL,
        'X-Auth-Key': CF_API_KEY,
        'Content-Type': 'application/json',
    }

    params = {
        'comment.contains': comment_key,
    }

    LOGGER.info(f"Fetching DNS record with comment key: {comment_key}")
    response = requests.get(f'{BASE_URL}zones/{zone_id}/dns_records', headers=headers, params=params)

    if response.status_code == 200:
        records = response.json()['result']
        if records:
            return records
    else:
        LOGGER.error(f"Failed to get dns_records with comment key: {response.json()}")

    return None


# Update the DNS record
def update_dns_record(record_id, zone_id, name, record_type, content, ttl=120, proxied=True):
    headers = {
        'X-Auth-Email': CF_EMAIL,
        'X-Auth-Key': CF_API_KEY,
        'Content-Type': 'application/json',
    }

    data = {
        'type': record_type,
        'name': name,
        'content': content,
        'ttl': ttl,
        'proxied': proxied,
    }

    response = requests.put(f'{BASE_URL}zones/{zone_id}/dns_records/{record_id}', json=data, headers=headers)

    if response.status_code == 200:
        LOGGER.info(f"DNS record updated successfully: {name} ({record_type}) -> {content}")
    else:
        LOGGER.error(f"Failed to update DNS record: {response.json()}")


# Loads static wishlist of domains in json format along with their metadata
def read_domains_from_file(json_file_path, zone_id):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    for domain in data:
        for key, value in domain.items():
            if isinstance(value, str):
                domain[key] = value.replace('$CF_ZONE_ID', zone_id)

    return data


# Get public IP address from the list of IP checking services
def get_public_ip():
    for service in IP_CHECK_SERVICES:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except requests.exceptions.RequestException:
            continue
    return None


# Check if there is an active internet connection
def is_connected():
    try:
        host = socket.gethostbyname("www.cloudflare.com")
        socket.create_connection((host, 80), 2)
        return True
    except Exception:
        pass
    return False

# Function to run the check and update process
def check_and_update_dns():
    if not is_connected():
        LOGGER.error("No internet connection. Skipping check and update.")
        return

    if len(CF_ZONE_ID) == 0:
        LOGGER.error("CF_ZONE_ID: At least one zone id must be set.")
        return
    elif len(CF_EMAIL) == 0:
        LOGGER.error("CF_EMAIL Missing: You have to provide your Cloudflare email.")
        return
    elif len(CF_API_KEY) == 0:
        LOGGER.error("CF_API_KEY Missing: You have to provide your Cloudflare API Key.")
        return
    elif len(DNS_RECORD_COMMENT_KEY) == 0 and len(DOMAINS_FILE_PATH) == 0:
        LOGGER.error("DNS_RECORD_COMMENT_KEY and DOMAINS_FILE_PATH are missing, don't know which domains to update")
        return

    public_ip = get_public_ip()
    domains_to_update = []

    if DNS_RECORD_COMMENT_KEY:
        LOGGER.info(f"Using DNS_RECORD_COMMENT_KEY='{DNS_RECORD_COMMENT_KEY}' to find DNS records to update.")
        domains_to_update = get_dns_records_by_comment(CF_ZONE_ID, DNS_RECORD_COMMENT_KEY)
    else:
        LOGGER.info(f"Using DOMAINS_FILE_PATH='{DOMAINS_FILE_PATH}' to find DNS records to update.")
        domains_to_update = read_domains_from_file(DOMAINS_FILE_PATH, CF_ZONE_ID)


    if public_ip:
        for domain_data in domains_to_update:
            print(domain_data)
            zone_id = domain_data['zone_id']
            domain_name = domain_data['name']
            proxied = domain_data['proxied']

            record = get_dns_record(zone_id, domain_name)

            if record:
                if public_ip != record['content']:
                    update_dns_record(
                        record['id'],
                        record['zone_id'],
                        domain_name,
                        record['type'],
                        public_ip,
                        proxied=proxied
                    )
                else:
                    LOGGER.info(f"IP addresses are the same for {domain_name}. No update needed.")
            else:
                # TODO: Add more logs, this error could also appear if the API Login fails
                LOGGER.error(f"DNS record for {domain_name} not found.")
    else:
        LOGGER.error("Failed to retrieve public IP. Skipping check and update.")


# Schedule the check and update process to run every 5 minutes
schedule.every(SCHEDULE_MINUTES).minutes.do(check_and_update_dns).run()

# Main loop
while True:
    schedule.run_pending()
    time.sleep(1)
