## How to run this repo
- Run promethues

    `docker run -d -p 9090:9090 --name prometheus -v /home/ubuntu/prometheus/prometheus:/etc/prometheus prom/prometheus`

- Run node exporter

    `docker run -d -p 9101:9100 --name node_exporter prom/node-exporter`

- Run grafana

    `docker run -d -p 3000:3000 --name grafana -v grafana_data:/var/lib/grafana grafana/grafana`

- Run alertmanager
```bash
    docker run -d \
    --name alertmanager \
    -p 9093:9093 \
    -v /home/ubuntu/prometheus/alertmanager:/etc/alertmanager \
    -v alertmanager-data:/alertmanager \
    prom/alertmanager \
    --config.file=/etc/alertmanager/alertmanager.yml \
    --storage.path=/alertmanager
```