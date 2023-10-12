# Step 1:
```bash
$ mkdir -p $(pwd)/prom-eu1 && docker run -i quay.io/thanos/thanosbench:v0.2.0-rc.1 block plan -p continuous-365d-tiny --labels 'cluster="eu1"' --max-time=6h | docker run -v $(pwd)/prom-eu1:/prom-eu1 -i quay.io/thanos/thanosbench:v0.2.0-rc.1 block gen --output.dir prom-eu1

$ sudo ls -lR $(pwd)/prom-eu1

$ cat <<EOF>> prometheus0_eu1.yml
global:
  scrape_interval: 5s
  external_labels:
    cluster: eu1
    replica: 0
    tenant: team-eu # Not needed, but a good practice if you want to grow this to multi-tenant system some day.

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['127.0.0.1:8080']
  - job_name: 'sidecar'
    static_configs:
      - targets: ['127.0.0.1:18080']
  - job_name: 'minio'
    metrics_path: /minio/prometheus/metrics
    static_configs:
      - targets: ['127.0.0.1:8000']
  - job_name: 'querier'
    static_configs:
      - targets: ['127.0.0.1:8081']
  - job_name: 'store_gateway'
    static_configs:
      - targets: ['127.0.0.1:18081']
EOF

docker run -d --net=host --rm \
    -v $(pwd)/prometheus0_eu1.yml:/etc/prometheus/prometheus.yml \
    -v $(pwd)/prom-eu1:/prometheus \
    -u root \
    --name prometheus-0-eu1 \
    quay.io/prometheus/prometheus:v2.38.0 \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.retention.time=1000d \
    --storage.tsdb.path=/prometheus \
    --storage.tsdb.max-block-duration=2h \
    --storage.tsdb.min-block-duration=2h \
    --web.listen-address=:8080 \
    --web.enable-lifecycle \
    --web.enable-admin-api

docker run -d --net=host --rm \
    --name prometheus-0-eu1-sidecar \
    -u root \
    quay.io/thanos/thanos:v0.28.0 \
    sidecar \
    --http-address 0.0.0.0:18080 \
    --grpc-address 0.0.0.0:18180 \
    --prometheus.url http://poc-lead.ovng.dev.myovcloud.com:8080

docker run -d --net=host --rm \
    --name querier \
    quay.io/thanos/thanos:v0.28.0 \
    query \
    --http-address 0.0.0.0:8081 \
    --query.replica-label replica \
    --store dns+poc-lead.ovng.dev.myovcloud.com:18180

Setup Verification
Once started you should be able to reach the Prometheus instance here and query.. 1 year of data!
Prometheus-0 EU1 page
Querier UI Store page.
```

# Step 2 Object Storage Continuous Backup
```bash
sudo mkdir /root/minio && \
docker run -d --rm --name minio \
     -v /root/minio:/data \
     -p 8000:9000 -e "MINIO_ACCESS_KEY=minio" -e "MINIO_SECRET_KEY=melovethanos" \
     minio/minio:RELEASE.2019-01-31T00-31-19Z \
     server /data

sudo mkdir /root/minio/thanos

docker stop prometheus-0-eu1-sidecar && \
docker run -d --net=host --rm \
    -v $(pwd)/bucket_storage.yaml:/etc/thanos/minio-bucket.yaml \
    -v $(pwd)/prom-eu1:/prometheus \
    --name prometheus-0-eu1-sidecar \
    -u root \
    quay.io/thanos/thanos:v0.28.0 \
    sidecar \
    --tsdb.path /prometheus \
    --objstore.config-file /etc/thanos/minio-bucket.yaml \
    --shipper.upload-compacted \
    --http-address 0.0.0.0:18080 \
    --grpc-address 0.0.0.0:18180 \
    --prometheus.url http://poc-lead.ovng.dev.myovcloud.com:8080
```
open Minio server UI to check data created on that

# Step 3 - Fetching metrics from Bucket
```bash
docker run -d --net=host --rm \
    -v $(pwd)/bucket_storage.yaml:/etc/thanos/minio-bucket.yaml \
    --name store-gateway \
    quay.io/thanos/thanos:v0.28.0 \
    store \
    --objstore.config-file /etc/thanos/minio-bucket.yaml \
    --http-address 0.0.0.0:18081 \
    --grpc-address 0.0.0.0:18181

docker stop querier && \
docker run -d --net=host --rm \
   --name querier \
   quay.io/thanos/thanos:v0.28.0 \
   query \
   --http-address 0.0.0.0:8081 \
   --query.replica-label replica \
   --store dns+poc-lead.ovng.dev.myovcloud.com:18180 \
   --store dns+poc-lead.ovng.dev.myovcloud.com:18181
```

# Step 4 - Thanos Compactor
```bash
docker run -d --net=host --rm \
    -v $(pwd)/bucket_storage.yaml:/etc/thanos/minio-bucket.yaml \
    --name thanos-compact \
    quay.io/thanos/thanos:v0.28.0 \
    compact \
    --wait --wait-interval 30s \
    --consistency-delay 0s \
    --objstore.config-file /etc/thanos/minio-bucket.yaml \
    --http-address 0.0.0.0:18085
```