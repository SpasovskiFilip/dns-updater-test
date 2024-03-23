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

Edit the `.env` file and replace the placeholders for `CF_API_TOKEN`, `CF_ZONE_ID`, `DNS_RECORD_COMMENT_KEY`, and the `domains.json` list with your actual data.


Example configuration for `domains.json`:
```
{
    "zones": [
        {
            "id": "$CF_ZONE_ID1",
            "domains":
            [
                {
                    "name": "example1.tuxhub.cloud"
                },
                {
                    "name": "example2.tuxhub.cloud"
                }

            ]
        },
        {
            "id": "$CF_ZONE_ID2",
            "domains":
            [
                {
                    "name": "sub1.hubtux.cloud"
                },
                {
                    "name": "sub2.hubtux.cloud"
                }

            ]
        }
    ]
}
```
Example configuration for `.env`:
```
CF_API_TOKEN=your_account_api_token
CF_ZONE_ID=your_cf_zone_id
CF_ZONE_ID1=your_cf_zone_id_1
CF_ZONE_ID1=your_cf_zone_id_2
DNS_RECORD_COMMENT_KEY=your_record_comment
DOMAINS_FILE_PATH=.\domains.json
SCHEDULE_MINUTES=60
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
Optional - Run the Docker container with binding the `main.py` file, but replace the `/path/to/local/` with the actual path to your local `main.py` file:
```
docker run -d --name dns-updater -v /path/to/local/main.py:/app/main.py --restart unless-stopped dns-updater
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
4. [OPTIONAL] If you have multiple zones, repeat steps 1-3 for each zone.

[Here](https://blog.devgenius.io/dns-updater-a-solution-for-managing-dynamic-ips-with-cloudflare-31be2f85d9fb) is a guide that shows you how to set up this tool.

https://blog.devgenius.io/dns-updater-a-solution-for-managing-dynamic-ips-with-cloudflare-31be2f85d9fb