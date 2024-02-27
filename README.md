# DNS Updater

DNS Updater is a Python-based tool that automatically updates Cloudflare DNS records with your public IP address. If your server's IP address changes frequently or you have dynamic ip, this tool ensures that your domains and subdomains always point to the correct server. It can handle multiple domains and subdomains from multiple zones, with proxying enabled or disabled. The tool runs checks and updates every 5 minutes and includes redundancy for IP checking services.

## Features

- Update multiple domains/subdomains from different zones
- Enable or disable proxying for each domain
- Redundancy for IP checking services
- Automatically runs checks and updates every 5 minutes
- Docker support for easy deployment

## Prerequisites

- Python 3.11
- Docker (optional)

## Installation

Clone the repository:

```
git clone https://github.com/alexplesoiu/dns-updater.git
cd dns-updater
```


Install the required Python packages:
```
pip install -r requirements.txt
```

## Configuration

Edit the `main.py` script and replace the placeholders for `API_TOKEN`, `ZONE_ID_1`, `ZONE_ID_2` (or however many zones you have), and the `DOMAINS_TO_UPDATE` list with your actual data.

Example configuration:
```
API_TOKEN = 'your_cloudflare_api_token'
ZONE_ID_1 = 'your_zone_1_id'
ZONE_ID_2 = 'your_zone_2_id'
DOMAINS_TO_UPDATE = [
    {
        'zone_id': ZONE_ID_1,
        'domain': 'subdomain1.example.com',
        'proxied': True
    },
    {
        'zone_id': ZONE_ID_1,
        'domain': 'subdomain2.example.com',
        'proxied': False
    },
    {
        'zone_id': ZONE_ID_2,
        'domain': 'subdomain.example.org',
        'proxied': True
    }
]
```

## Usage
Run the script:

```
python main.py
```

## Docker Deployment
Build the Docker container:

```
docker build -t dns-updater .
```

Run the Docker container:
```
docker run -d --name dns-updater --restart unless-stopped dns-updater
```

This will run the container in detached mode and ensure it starts automatically when the server restarts, unless you explicitly stop it.

## Tutorial
### 🔑 How to create and get an API Token from Cloudflare
1. Log in to your Cloudflare account.
2. Navigate to your profile settings by clicking on your account icon in the top right corner of the dashboard.
3. Navigate to the “API Tokens” link from the left side menu.
4. Click the Create Token under User API Tokens.
5. Under Templates use the Edit zone DNS template.
6. Rename the token to your liking and change the Zone resources to Include All zones.
7. Continue to summary and then Create token
8. Copy the token shown. This is your API_TOKEN.
9. ⚠️ ***THIS TOKEN WILL BE SHOWN ONLY ONCE. DO NOT FORGET TO SAVE IT!*** ⚠️

### 🌍 Obtaining the Zone ID
To obtain the Zone ID for your domain from Cloudflare, follow these steps:
1. Log in to your Cloudflare account.
2. Select the domain you want to manage from the list of domains in your dashboard.
3. On the domain’s overview page, you will find the Zone ID displayed in the right-hand sidebar under the “API” section. This is your Zone ID for your domain.

[Here](https://blog.devgenius.io/dns-updater-a-solution-for-managing-dynamic-ips-with-cloudflare-31be2f85d9fb) is a guide that shows you how to set up this tool.

https://blog.devgenius.io/dns-updater-a-solution-for-managing-dynamic-ips-with-cloudflare-31be2f85d9fb
