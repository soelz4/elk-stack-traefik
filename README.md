# ELK Stack with Treafik

The ELK Stack is a powerful suite for centralized logging and data analysis. **Filebeat** acts as a lightweight shipper, collecting logs from your servers and applications. It forwards these logs to a **Kafka** cluster, which provides a resilient message buffer for handling high-throughput data. **Logstash** then consumes the logs from Kafka, parsing and enriching them into a structured format. The processed data is indexed and stored in **ElasticSearch**, a highly scalable search and analytics engine. Finally, **Kibana** provides a web-based visualization interface to explore the data and create insightful dashboards. In this architecture, **Traefik** is used as a modern reverse proxy and API gateway. It efficiently routes external traffic to the appropriate services, such as Kibana, while also handling SSL/TLS termination. This creates a robust, scalable, and observable pipeline for managing log data from source to insight.

## Overview

PowerDNS Service Schema

![SCHEMA](./png/scheme.png "ELK Schema")

## Prerequisites

1 - **[Docker](https://www.docker.com/)**

2 - **[Docker Compose](https://docs.docker.com/compose/)**

3 - **Docker Images**

- [postgres](https://hub.docker.com/_/postgres)
- [filebeat](https://hub.docker.com/r/elastic/filebeat)
- [kafka](https://hub.docker.com/r/apache/kafka)
- [kafka-ui](https://hub.docker.com/r/provectuslabs/kafka-ui)
- [logstash](https://hub.docker.com/_/logstash)
- [elasticsearch](https://hub.docker.com/_/elasticsearch)
- [kibana](https://hub.docker.com/_/kibana)

## Docker Compose

```yaml
services:
  postgres:
    image: postgres:17-alpine3.22
    container_name: postgres
    restart: always
    ports:
      - "5432:5432"
    networks:
      - elk
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - /var/lib/pgsql/data:/var/lib/postgresql/data
  traefik:
    image: traefik:v3.4
    container_name: traefik
    ports:
      - "80:80"
      - "443:443"
      # - "8080:8080"
    networks:
      - proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./traefik/traefik.yaml:/etc/traefik/traefik.yaml:ro
      - ./traefik/dynamic:/etc/traefik/dynamic:ro
      - ./traefik/certs:/certs:ro
  filebeat:
    image: elastic/filebeat:8.19.7
    container_name: filebeat
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_started
    networks:
      - elk
    volumes:
      - ./filebeat/filebeat.yaml:/usr/share/filebeat/filebeat.yml:ro
      # - ./filebeat/modules.d:/usr/share/filebeat/modules.d:ro
      - /var/lib/pgsql/data/log:/var/lib/pgsql/data/log:ro
  kafka:
    image: apache/kafka:4.1.0
    container_name: kafka
    networks:
      - elk
    # ports:
    # - "9092:9092"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka:9093"
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_METRICS_PORT: 9997
      KAFKA_JMX_PORT: 9997
      KAFKA_NUM_PARTITIONS: 1
      # optional but nice to keep stable across restarts
      CLUSTER_ID: "5L6g3nShT-eMCtK--X86sw"
    volumes:
      - kafka-data:/var/lib/kafka/data
  kafka-ui:
    image: provectuslabs/kafka-ui:master
    container_name: kafka-ui
    networks:
      - proxy
      - elk
    # ports:
    # - "8080:8080"
    environment:
      - KAFKA_CLUSTERS_0_NAME=local
      - KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka:9092
      - KAFKA_CLUSTERS_0_METRICS_PORT=9997
      - KAFKA_CLUSTERS_0_KRAFT_ENABLED=true
      - SERVER_SERVLET_CONTEXT_PATH=/kafka
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_started
  logstash:
    image: logstash:8.19.7
    container_name: logstash
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_started
      elasticsearch:
        condition: service_started
    networks:
      - elk
    volumes:
      - ./logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
    # ports:
    # - "5044:5044"
  elasticsearch:
    image: elasticsearch:8.19.7
    container_name: elasticsearch
    networks:
      - elk
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
      - xpack.security.enabled=false
      - xpack.security.http.ssl.enabled=false
      - xpack.ml.enabled=false
    # ports:
    # - "9200:9200"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - es-data:/usr/share/elasticsearch/data
  kibana:
    image: kibana:8.19.7
    container_name: kibana
    depends_on:
      postgres:
        condition: service_healthy
      elasticsearch:
        condition: service_started
    networks:
      - elk
      - proxy
    # ports:
    # - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - ELASTICSEARCH_SERVICEACCOUNTTOKEN=AAEAAWVsYXN0aWMva2liYW5hL2tpYmFuYS10b2tlbjpCaERuWEN3clRULXVQREs1Mzk0WV93
      - ELASTICSEARCH_SSL_CERTIFICATEAUTHORITIES=/usr/share/kibana/config/certs/http_ca.crt
      - SERVER_BASEPATH=/kibana
      - SERVER_REWRITEBASEPATH=true
    volumes:
      - ./kibana/certs/http_ca.crt:/usr/share/kibana/config/certs/http_ca.crt:ro

networks:
  proxy:
    driver: bridge
    external: true
  elk:
    driver: bridge
    external: true

volumes:
  es-data:
  kafka-data:
```

## Traefik

> [!WARNING] > **⚠️ Security Notice:** This setup uses self-signed TLS certificates for Traefik. For any environment other than local development, you must provide your own valid certificates.

Traefik serves as the modern reverse proxy and API gateway for the entire ELK stack infrastructure, handling SSL termination, routing, and service discovery.

### 🎯 Configuration Overview

**Global Settings:**

- **Dashboard**: Enabled with secure access at `/dashboard`
- **Log Level**: DEBUG for detailed troubleshooting
- **Entry Points**:
  - `web` (Port 80): HTTP traffic with automatic redirect to HTTPS
  - `websecure` (Port 443): HTTPS traffic with TLS encryption

**Provider Configuration:**

- **Docker**: Auto-discovers services on the `proxy` network
- **File**: Dynamic configuration from `/etc/traefik/dynamic` with live reload

traefik global settings ~> `traefik.yaml`

```yaml
global:
  checkNewVersion: false
  sendAnonymousUsage: false
log:
  level: DEBUG
api:
  dashboard: true
  # insecure: true
entryPoints:
  web:
    address: :80
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: :443
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: "proxy"
  file:
    directory: "/etc/traefik/dynamic"
    watch: true
```

### 🔐 Security & Access Control

**TLS Configuration:**

```yaml
tls:
  certificates:
    - certFile: /certs/local.crt
    - keyFile: /certs/local.key
```

### 🔐 Protected Routes

- **Traefik Dashboard**: `/dashboard` paths with redirect middleware
- **Kibana**: Secure access via `/kibana` path
- **Kafka UI**: Management interface at `/kafka` path

### 🛣️ Routing Rules

| Service           | Path         | EntryPoint | TLS | Description                  |
| ----------------- | ------------ | ---------- | --- | ---------------------------- |
| Traefik Dashboard | `/dashboard` | websecure  | ✅  | Internal API & management UI |
| Kibana            | `/kibana`    | websecure  | ✅  | Data visualization dashboard |
| Kafka UI          | `/kafka`     | websecure  | ✅  | Kafka cluster management     |

routing configuration ~> `rules.yaml`

```yaml
http:
  routers:
    traefik-dashboard:
      rule: "PathPrefix(`/api`) || PathPrefix(`/dashboard`)"
      service: api@internal
      entryPoints:
        - websecure
      tls: {}
      middlewares:
        - dashboard
    kafka-ui:
      entryPoints:
        - websecure
      service: kafka-ui
      rule: "PathPrefix(`/kafka`)"
      tls: {}
    kibana:
      entryPoints:
        - websecure
      service: kibana
      rule: "PathPrefix(`/kibana`)"
      tls: {}

  middlewares:
    dashboard:
      redirectRegex:
        regex: "^(https?://[^/]+/dashboard)$"
        replacement: "${1}/"
        permanent: true

  services:
    kafka-ui:
      loadBalancer:
        servers:
          - url: "http://kafka-ui:8080"
        passHostHeader: true
    kibana:
      loadBalancer:
        servers:
          - url: "http://kibana:5601"
        passHostHeader: true
```

### 🔄 Middleware Features

**Dashboard Redirect Middleware:**

- Ensures proper trailing slashes for dashboard URLs
- Permanent redirect for clean URL structure
- Enhanced user experience for the management interface

### 🌐 Service Discovery

**Docker Integration:**

- Monitors Docker socket for container changes
- `exposedByDefault: false` for enhanced security
- Uses `proxy` network for service communication

**Load Balancer Configuration:**

- **Kibana**: Routes to `http://kibana:5601`
- **Kafka UI**: Routes to `http://kafka-ui:8080`
- `passHostHeader: true` for proper header propagation

## Filebeat

```yaml
filebeat.modules:
  - module: postgresql
    log:
      enabled: true
      var.paths:
        # - /var/log/postgresql/postgresql-*.log
        - /var/lib/pgsql/data/log/postgresql-*.log

processors:
  - add_fields:
      target: ""
      fields:
        source_type: postgresql

output.kafka:
  hosts: ["kafka:9092"]
  topic: "pg-logs"
  required_acks: 1
  compression: gzip
  max_message_bytes: 1000000
```

## Logstash

```conf
input {
  kafka {
    bootstrap_servers => "kafka:9092"
    topics => ["pg-logs"]
    group_id => "logstash-pg"
    decorate_events => false
    codec => "json"
  }
}

filter {
  mutate {
    add_field => { "ingest_pipeline" => "logstash-pg" }
  }
}

output {
  elasticsearch {
    hosts  => ["http://elasticsearch:9200"]
    index  => "pg-logs-%{+YYYY.MM.dd}"
    retry_initial_interval => 5
    retry_max_interval => 30
    retry_on_conflict => 5
    ssl => false
  }
}
```

## Run

1 - Clone the Repo

```bash
git clone https://github.com/soelz4/elk-stack-traefik.git
```

```bash
cd elk-stack-traefik
```

```bash
vim .env
```

```.env
# ----- POSTGRES -----
POSTGRES_HOST=<host>
POSTGRES_USER=<postgres-user>
POSTGRES_PASSWORD=<postgres-password>
POSTGRES_DB=<postgres-db>
```

2 - Run with Docker Compose

```bash
docker compose up -d
```

## 📊 Test Data Generator

The `log-generator` directory contains a Python script that simulates real-world application activity by continuously generating sample user data and inserting it into PostgreSQL. This creates a consistent stream of log data for testing the ELK stack pipeline.

### 🎯 Purpose

- Generates continuous test data for ELK stack validation
- Simulates user activity in a PostgreSQL database
- Provides a reliable data source for pipeline monitoring
- Creates sample logs for Kibana visualization testing

### 🚀 Usage

```bash
cd log-generator
```

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
python data_generator.py
```
