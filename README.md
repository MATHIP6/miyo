# Miyo

A lightweight DNS server that automatically resolves domains for Docker containers based on labels.

## Overview

Miyo acts as a DNS proxy that dynamically registers domains from running Docker containers. Any container with a `dns.domain` label will have its domain automatically resolved to your host's IP address. All other DNS queries are forwarded to an upstream DNS server.

## Features

- Automatic DNS record registration via Docker container labels
- Real-time container event monitoring (create/kill)
- DNS proxy with configurable upstream server
- Dockerized deployment

## Quick Start

### Using Docker Compose

1. Clone the repository:

```bash
git clone <repository-url>
cd miyo
```

2. Build the image:

```bash
docker build -t miyo .
```

3. Run with Docker Compose:

```bash
docker compose up -d
```

4. Configure your system or router to use Miyo as the DNS server (default port: `8080` mapped to container port `53`).

### Using Environment Variables

| Variable | Description | Default |
|---|---|---|
| `HOST_ADDRESS` | The IP address returned for registered container domains | `127.0.0.1` |
| `UPSTREAM_DNS` | Upstream DNS server for non-registered domains | `1.1.1.1` |
| `UPSTREAM_DNS_PORT` | Upstream DNS server port | `53` |

## Usage

### Registering a Container Domain

Add the `dns.domain` label to any Docker container:

```bash
docker run -d --label dns.domain=myapp.local nginx
```

With Docker Compose:

```yaml
services:
  myapp:
    image: nginx
    labels:
      - dns.domain=myapp.local
```

The domain `myapp.local` will automatically resolve to the configured `HOST_ADDRESS`.

## Requirements

- Docker
- Docker Compose (optional)
- Python 3.10+ (for local development)

## License

See [LICENSE](LICENSE) for details.
