# galloper
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Fcarrier-io%2Fgalloper.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Fcarrier-io%2Fgalloper?ref=badge_shield)

container that provide email, slack notification and analytics services

## Local Dev setup

install all required packages 
```shell script
pip install -r requirements.txt
pip install celery==4.3.0 kombu==4.5.0 selenium==3.141.0 vine==1.3.0
pip install git+https://github.com/carrier-io/control_tower.git
```

Set `local_dev` variable to `True` in `galloper/constants.py` 

Copy `cp local_dev/postgreschema.sh /tmp`

Create directory `mkdir /tmp/tasks`

start postgres container 

```
docker run -v /tmp/postgreschema.sh:/docker-entrypoint-initdb.d/postgreschema.sh \
           -e POSTGRES_DB=carrier -e POSTGRES_USER=carrier \
           -e POSTGRES_PASSWORD=password -e POSTGRES_SCHEMAS=carrier,keycloak \ 
           -e POSTGRES_INITDB_ARGS=--data-checksums \
           -p 5432:5432 \
           postgres:12.2
```

start vault container
```
docker run -e 'VAULT_LOCAL_CONFIG={"disable_mlock":true,"listener":{"tcp":{"address":"0.0.0.0:8200","tls_disable": 1}},"storage":{"file":{"path":"/tmp/data"}},"ui":false}' \
           -p 8200:8200 \
           vault:latest \
           vault server -config=/vault/config/local.json
```
start minio container
```
docker run -p 9000:9000 \
  -e "MINIO_ACCESS_KEY=admin" \
  -e "MINIO_SECRET_KEY=password" \
  minio/minio::RELEASE.2019-10-12T01-39-57Z server /data
```

start redis container
```
docker run -p 6379:6379 --entrypoint="redis-server --requirepass password" redis:5.0.7
```

in pycharm terminal run celery worker 
```
celery -A galloper.celeryapp worker -l info -c%s --max-tasks-per-child 1
```

Start application
```shell script
python app.py
```

This is pretty much it


To run the tasks like performance tests you need to spend a bit more time configuring application endpoints in secrets, start interceptors and/or observer-hub+router
