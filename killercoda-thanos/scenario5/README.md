for i in $(seq 0 2); do 
docker run -d --net=host \
 -v $(pwd)/prometheus"${i}".yml:/etc/prometheus/prometheus.yml \
 -v $(pwd)/prometheus_data/prometheus"${i}":/prometheus"${i}" \
 -u root\
 --name prometheus"${i}" \
 quay.io/prometheus/prometheus:v2.38.0 \
 --config.file=/etc/prometheus/prometheus.yml \
 --storage.tsdb.path=/prometheus"${i}" \
 --web.listen-address=:808"${i}" \
 --web.enable-lifecycle \
 --web.enable-admin-api && echo "Prometheus ${i} started!"
done

==============================================================
for i in $(seq 0 2); do
docker run -d --net=host \
 -v $(pwd)/prometheus"${i}".yml:/etc/prometheus/prometheus.yml \
 --name prometheus-sidecar"${i}" \
 -u root \
 quay.io/thanos/thanos:v0.28.0 \
 sidecar \
 --http-address=0.0.0.0:1808"${i}" \
 --grpc-address=0.0.0.0:1818"${i}" \
 --reloader.config-file=/etc/prometheus/prometheus.yml \
 --prometheus.url=http://poc-m4.ovng.dev.myovcloud.com:808"${i}" && echo "Started Thanos Sidecar for Prometheus ${i}!"
done

==============================================================
docker run -d --net=host \
	--name querier \
	quay.io/thanos/thanos:v0.28.0 \
	query \
	--http-address 0.0.0.0:10812 \
	--grpc-address 0.0.0.0:10801 \
	--query.replica-label replica \
	--store poc-m4.ovng.dev.myovcloud.com:18180 \
	--store poc-m4.ovng.dev.myovcloud.com:18181 \
	--store poc-m4.ovng.dev.myovcloud.com:18182 & echo "Started Thanos Querier

server {
  listen 10802;
  server_name proxy;
  location / {
    echo_exec @default;
  }

  location ^~ /api/v1/ {
    echo_sleep 5;
    echo_exec @default;
  }

  location @default {
    proxy_pass http://poc-m4.ovng.dev.myovcloud.com:10812;
  }
}


docker run -d --net=host \
    -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf \
    --name nginx \
    yannrobert/docker-nginx && echo "Started Querier Proxy!"



docker run -d --net=host \
	-v $(pwd)/frontend.yml:/etc/thanos/frontend.yml \
	--name query-frontend \
	quay.io/thanos/thanos:v0.28.0 \
	query-frontend \
	--http-address 0.0.0.0:20802 \
	--query-frontend.compress-responses \
	--query-frontend.downstream-url=http://poc-m4.ovng.dev.myovcloud.com:10802 \
	--query-frontend.log-queries-longer-than=5s \
	--query-range.split-interval=1m \
	--query-range.response-cache-max-freshness=1m \
	--query-range.max-retries-per-request=5 \
	--query-range.response-cache-config-file=/etc/thanos/frontend.yml \
	--cache-compression-type="snappy" && echo "Started Thanos Query Frontend"