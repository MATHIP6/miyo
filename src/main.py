import os
import socket
import dnslib
import docker
from docker.client import DockerClient
from docker.models.containers import Container
import threading
import logging

records = []

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

UPSTREAM_DNS = (
    os.getenv("UPSTREAM_DNS") or "1.1.1.1",
    os.getenv("UPSTREAM_DNS_PORT") or 53,
)


def get_host_address():
    return os.getenv("HOST_ADDRESS") or "127.0.0.1"


def get_records(client: DockerClient):
    for container in client.containers.list():
        container: Container
        domain = container.labels.get("dns.domain")
        if domain:
            records.append(domain)


def handle_docker_events(client: DockerClient):
    for event in client.events(decode=True):
        if event["Type"] != "container":
            return
        container_id = event["Actor"]["ID"]
        container: Container = client.containers.get(container_id)
        domain = container.labels.get("dns.domain")
        if domain:
            if event["Action"] == "create":
                records.append(domain)
            elif event["Action"] == "kill":
                records.remove(domain)


def forward(record: dnslib.DNSRecord):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(record.pack(), UPSTREAM_DNS)
    response, _ = sock.recvfrom(4096)
    return response


def main():
    logging.info("starting app...")
    get_host_address()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 53))
    client = docker.from_env()
    logging.info("getting records")
    get_records(client)
    threading.Thread(target=handle_docker_events, args=(client,), daemon=True).start()
    while True:
        data, addr = sock.recvfrom(512)
        try:
            message = dnslib.DNSRecord.parse(data)
            req_domain = str(message.q.qname)[:-1]
            response = None
            for domain in records:
                if domain == req_domain:
                    response = message.reply()
                    response.add_answer(
                        *dnslib.RR.fromZone(domain + " A " + get_host_address())
                    )
                    sock.sendto(response.pack(), addr)
                    break
            if not response:
                response = forward(message)
                sock.sendto(response, addr)
        except dnslib.DNSError:
            logging.warning("Warning: Invalid packet received")


if __name__ == "__main__":
    main()
