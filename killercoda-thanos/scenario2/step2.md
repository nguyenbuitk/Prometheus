Step 2 - Object Storage Continuous Backup
Maintaining one year of data within your Prometheus is doable, but not easy. It's tricky to resize, backup or maintain this data long term. On top of that Prometheus does not do any replication, so any unavailability of Prometheus results in query unavailability.

This is where Thanos comes to play. With a single configuration change we can allow Thanos Sidecar to continuously upload blocks of metrics that are periodically persisted to disk by the Prometheus.

NOTE: Prometheus when scraping data, initially aggregates all samples in memory and WAL (on-disk write-head-log). Only after 2-3h it "compacts" the data into disk in form of 2h TSDB block. This is why we need to still query Prometheus for latest data, but overall with this change we can keep Prometheus retention to minimum. It's recommended to keep Prometheus retention in this case at least 6 hours long, to have safe buffer for a potential event of network partition.
Starting Object Storage: Minio
Let's start simple S3-compatible Minio engine that keeps data in local disk:
```bash
mkdir /root/minio && \
docker run -d --rm --name minio \
     -v /root/minio:/data \
     -p 9000:9000 -e "MINIO_ACCESS_KEY=minio" -e "MINIO_SECRET_KEY=melovethanos" \
     minio/minio:RELEASE.2019-01-31T00-31-19Z \
     server /data
```
Create thanos bucket:
```bash
mkdir /root/minio/thanos
```
Verification
To check if the Minio is working as intended, let's open Minio server UI

Enter the credentials as mentioned below:

Access Key = minio Secret Key = melovethanos

Sidecar block backup
All Thanos components that use object storage uses the same objstore.config flag with the same "little" bucket config format.

Switch on to the Editor tab and make a bucket_storage.yaml file and paste the below code in it.
```bash
type: S3
config:
  bucket: "thanos"
  endpoint: "172.17.0.1:9000"
  insecure: true
  signature_version2: true
  access_key: "minio"
  secret_key: "melovethanos"
```
Let's restart sidecar with updated configuration in backup mode.

docker stop prometheus-0-eu1-sidecar
Thanos sidecar allows to backup all the blocks that Prometheus persists to the disk. In order to accomplish this we need to make sure that:

Sidecar has direct access to the Prometheus data directory (in our case host's /root/prom-eu1 dir) (--tsdb.path flag)
Bucket configuration is specified --objstore.config-file
--shipper.upload-compacted has to be set if you want to upload already compacted blocks when sidecar starts. Use this only when you want to upload blocks never seen before on new Prometheus introduced to Thanos system.
Let's run sidecar:
```bash
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
    --http-address 0.0.0.0:19090 \
    --grpc-address 0.0.0.0:19190 \
    --prometheus.url http://172.17.0.1:9090
```
Verification
We can check whether the data is uploaded into thanos bucket by visitng Minio. It will take couple of seconds to synchronize all blocks.

Once all blocks appear in the minio thanos bucket, we are sure our data is backed up. Awesome! 💪