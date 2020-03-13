#!/usr/bin/env python3

import os
import signal
import time
import requests
import json
import logging
from prometheus_client import start_http_server, Gauge


# Settings

token = os.getenv("TOKEN")
logLevel = os.getenv("LOG", "WARNING")

# Variables

nodeinfo = {}

# Configure Log system

numeric_level = getattr(logging, logLevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % logLevel)
logging.basicConfig(
    format='%(asctime)s :: %(levelname)s :: %(message)s', level=numeric_level)


# manage signal

def term_signal(signum, stack):
    print('Stop Sherlock Exporter')
    exit(0)


signal.signal(signal.SIGTERM, term_signal)

# Create a metric to track values.

totalMemoryKB = Gauge('sherlock_total_memory_kb',
                      'Total Memory in KB', ['name', 'id', 'version', 'ip'])
totalStorageKB = Gauge('sherlock_total_storage_kb',
                       'Total Storage in KB', ['name', 'id', 'version', 'ip'])
cpuUsage = Gauge('sherlock_cpu_usage', 'CPU Usage',
                 ['name', 'id', 'version', 'ip'])
memoryFreeKB = Gauge('sherlock_memory_free_kb',
                     'Memory Free in KB', ['name', 'id', 'version', 'ip'])
storageFreeKB = Gauge('sherlock_storage_free_kb',
                      'Storage Free in KB', ['name', 'id', 'version', 'ip'])

# Main Loop

start_http_server(8080)
logging.info("Launch sherlock exporter")

while True:

    url = "https://iot.nutanix.com/v1.0/nodesinfo/"
    headers = {'Authorization': 'Bearer ' + token}

    response = requests.request("GET", url, headers=headers)

    if response.ok:
        nodeinfojson = json.loads(response.text)["result"]
        logging.debug(nodeinfojson)
        for entry in nodeinfojson:
            id = entry["id"]
            nodeinfo[id] = entry
    else:
        logging.error("nodesinfo error: %s", response.content)

    url = "https://iot.nutanix.com/v1/edges"

    response = requests.request("GET", url, headers=headers)

    if response.ok:

        edgesList = json.loads(response.text)
        logging.debug(edgesList)

        for edge in edgesList:
            id = edge["id"]
            name = edge["name"]
            if "nodeVersion" in nodeinfo[id]:
                version = nodeinfo[id]["nodeVersion"]
                ipAddress = edge["ipAddress"]

                totalMemoryKB.labels(name=name, id=id, version=version, ip=ipAddress).set(
                    nodeinfo[id]["totalMemoryKB"])
                totalStorageKB.labels(name=name, id=id, version=version, ip=ipAddress).set(
                    nodeinfo[id]["totalStorageKB"])
                cpuUsage.labels(name=name, id=id, version=version,
                                ip=ipAddress).set(nodeinfo[id]["cpuUsage"])
                memoryFreeKB.labels(name=name, id=id, version=version, ip=ipAddress).set(
                    nodeinfo[id]["memoryFreeKB"])
                storageFreeKB.labels(name=name, id=id, version=version, ip=ipAddress).set(
                    nodeinfo[id]["storageFreeKB"])
    else:
        logging.error("edges error: %s", response.content)

    time.sleep(10)
