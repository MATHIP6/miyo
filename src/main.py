import socket
import dnslib
import docker
from docker.client import DockerClient
from docker.models.containers import Container
import dotenv
import threading
import logging

records = []

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_host_address():
    address = dotenv.dotenv_values(".env").get("HOST_ADDRESS")
    if address:
        logging.info("yeeep")
        return address
    else:
        logging.info("nooo")
        return socket.gethostbyname(socket.gethostname())


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


def main():
    logging.info("starting app...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 8080))
    client = docker.from_env()
    get_records(client)
    threading.Thread(target=handle_docker_events, args=(client,), daemon=True).start()
    while True:
        data, addr = sock.recvfrom(512)
        try:
            message = dnslib.DNSRecord.parse(data)
            req_domain = str(message.q.qname)[:-1]
            response = message.reply()
            for domain in records:
                if domain == req_domain:
                    response.add_answer(
                        *dnslib.RR.fromZone(domain + " A " + get_host_address())
                    )
            sock.sendto(response.pack(), addr)
        except dnslib.DNSError:
            logging.warning("Warning: Invalid packet received")


if __name__ == "__main__":
    main()
