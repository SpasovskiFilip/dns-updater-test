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
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ZONE_ID = os.getenv("CF_ZONE_ID")
DNS_RECORD_COMMENT_KEY = os.getenv('DNS_RECORD_COMMENT_KEY')
DOMAINS_FILE_PATH = os.getenv('DOMAINS_FILE_PATH')
SCHEDULE_MINUTES = int(os.getenv('SCHEDULE_MINUTES', 60))

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

    # Create formatters and add it to handlers
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
    LOGGER.info(f"Fetching record for '{domain_name}' in zone '{zone_id}.")

    headers = {
        'Authorization': 'Bearer ' + CF_API_TOKEN,
        'Content-Type': 'application/json',
    }

    params = {
        'name': domain_name,
    }

    response = requests.get(f'{BASE_URL}zones/{zone_id}/dns_records', headers=headers, params=params)

    if response.status_code == 200:
        records = response.json()['result']

        if records:
            LOGGER.info(f"Successfully fetched data for '{domain_name}'.")
            return records[0]
    else:
        LOGGER.error(f"Failed to fetch data for '{domain_name}'. Response: {response.json()}")

    return None


# Update the DNS record
def update_dns_record(record, content):
    headers = {
        'Authorization': 'Bearer ' + CF_API_TOKEN,
        'Content-Type': 'application/json',
    }

    data = {
        'content': content
    }

    response = requests.patch(
                f"{BASE_URL}zones/{record['zone_id']}/dns_records/{record['id']}",
                json=data,
                headers=headers
            )

    if response.status_code == 200:
        LOGGER.info(f"DNS record updated successfully: {record['name']} ({record['type']}) -> {content}")
    else:
        LOGGER.error(f"Failed to update DNS record: {response.json()}")


# Loads static wishlist of domains in json format along with their metadata
def read_zones_from_file(json_file_path, zone_id):
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    zones = data['zones']

    for zone in zones:
        if "$" in zone['id']:
            zone['id'] = zone_id

        for domain in zone['domains']:
            domain['zone_id'] = zone['id']

        LOGGER.info(f"Sucessfully read zone {zone}.")

    return zones


# Fetches all DNS records that were loaded from file
def get_dns_records_by_name(zones):
    records = []

    LOGGER.info(f"Trying to fetch records for {len(zones)} zones.")

    for zone in zones:
        for domain in zone['domains']:
            record = get_dns_record(domain['zone_id'], domain['name'])

            if record is not None:
                records.append(record)

    return records


# Fetches all DNS records that contain the comment key inside of the comment
def get_dns_records_by_comment(zone_id, comment_key):
    headers = {
        'Authorization': 'Bearer ' + CF_API_TOKEN,
        'Content-Type': 'application/json',
    }

    params = {
        'comment.contains': comment_key,
    }

    LOGGER.info(f"Fetching DNS record with comment key: {comment_key}")
    response = requests.get(f'{BASE_URL}zones/{zone_id}/dns_records', headers=headers, params=params)

    if response.status_code == 200:
        records = response.json()['result']
        if records and len(records) > 0:
            return records
        else:
            LOGGER.warning(f"Request was successful but no valid domains were found: {response.json()}")
            return []
    else:
        LOGGER.error(f"Failed to get dns_records with comment key: {response.json()}")

    return []


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
    LOGGER.info("Run triggered by schedule.")

    if not is_connected():
        LOGGER.error("No internet connection. Skipping check and update.")
        return

    if CF_ZONE_ID is None:
        LOGGER.error("CF_ZONE_ID: At least one zone id must be set.")
        return
    elif CF_API_TOKEN is None:
        LOGGER.error("CF_API_TOKEN Missing: You have to provide your Cloudflare API Token.")
        return
    elif DNS_RECORD_COMMENT_KEY is None and DOMAINS_FILE_PATH is None:
        LOGGER.error("DNS_RECORD_COMMENT_KEY and DOMAINS_FILE_PATH are missing, don't know which domains to update")
        return

    public_ip = get_public_ip()
    domain_records = []

    if DNS_RECORD_COMMENT_KEY is not None:
        LOGGER.info(f"Using DNS_RECORD_COMMENT_KEY='{DNS_RECORD_COMMENT_KEY}' to find DNS records to update.")
        domain_records = get_dns_records_by_comment(CF_ZONE_ID, DNS_RECORD_COMMENT_KEY)
    else:
        LOGGER.info(f"Using DOMAINS_FILE_PATH='{DOMAINS_FILE_PATH}' to find DNS records to update.")
        domain_records = get_dns_records_by_name(read_zones_from_file(DOMAINS_FILE_PATH, CF_ZONE_ID))

    valid_domains = [x['name'] for x in domain_records if x is not None]
    LOGGER.info(f"Found {len(valid_domains)} valid domains for update: [{','.join(valid_domains)}]")

    if public_ip:
        for record in domain_records:
            domain_name = record['name']

            if record is None:
                LOGGER.error(f"DNS record for {domain_name} not found.")
                continue

            if public_ip != record['content']:
                update_dns_record(
                    record,
                    public_ip
                )
            else:
                LOGGER.info(f"IP addresses are the same for {domain_name}. No update needed.")
    else:
        LOGGER.error("Failed to retrieve public IP. Skipping check and update.")


LOGGER.info(f"Schedule is set at {SCHEDULE_MINUTES}")

# Schedule the check and update process to run every X minutes
schedule.every(SCHEDULE_MINUTES).minutes.do(check_and_update_dns).run()

# Main loop
while True:
    schedule.run_pending()
    time.sleep(1)
