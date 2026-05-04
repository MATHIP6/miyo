import os
import dnslib
from dnslib.dns import DNSRecord
import docker
from docker.client import DockerClient
from docker.models.containers import Container
import threading
import logging
from dnslib.server import DNSHandler, DNSServer
from dnslib.proxy import ProxyResolver
import time

records = []

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
            handle_docker_events(client)
            return
        container_id = event["Actor"]["ID"]

        if event["Action"] == "create":
            container = client.containers.get(container_id)
            domain = container.labels.get("dns.domain")
            if domain:
                records.append(domain)
        elif event["Action"] == "kill":
            container = None

            for i_container in client.containers.list():
                if i_container.id == container_id:
                    container = i_container

            if container is None:
                handle_docker_events(client)
                return

            domain = container.labels.get("dns.domain")
            if domain:
                records.remove(domain)
    handle_docker_events(client)


class Resolverr(ProxyResolver):
    def __init__(self, upstream: str, port):
        self.upstream = upstream
        super().__init__(upstream, port, 5)

    def resolve(self, request: DNSRecord, handler: DNSHandler):
        reply = request.reply()
        handler.handle
        req_domain = str(request.q.qname)[:-1]
        for domain in records:
            if domain == req_domain:
                reply.add_answer(
                    *dnslib.RR.fromZone(domain + " A " + get_host_address())
                )
                return reply
        return super().resolve(request, handler)


def main():
    logger.info("starting app...")

    client = docker.from_env()
    logging.info("getting records")
    get_records(client)
    threading.Thread(target=handle_docker_events, args=(client,), daemon=True).start()

    resolverr = Resolverr(
        os.getenv("UPSTREAM_DNS") or "1.1.1.1", os.getenv("UPSTREAM_DNS_PORT") or 53
    )
    server = DNSServer(resolverr, get_host_address() or "", 53)
    server.start_thread()

    try:
        while server.isAlive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("stopping app...")
        server.stop()


if __name__ == "__main__":
    main()
