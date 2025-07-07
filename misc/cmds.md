CMDs for local testing before orchestrating the experiments with Python.

```bash
docker network create p2p
```

# Bootstrap Node

```bash
docker run --network waku -p 8645:8645 -p 8008:8008 wakuorg/nwaku \
 --listen-address=0.0.0.0 \
 --rest=true \
 --rest-admin=true \
 --rest-address=0.0.0.0 \
 --rest-port=8645 \
 --metrics-server=true \
 --metrics-server-address=0.0.0.0 \
 --metrics-server-port=8008
```

# Peer Node (replace multiaddr)

```bash
docker run --network waku -p 8646:8645 -p 8009:8008 wakuorg/nwaku \
 --listen-address=0.0.0.0 \
 --tcp-port=60000 \
 --rest=true \
 --rest-admin=true \
 --rest-address=0.0.0.0 \
 --rest-address=0.0.0.0 \
 --rest-port=8645 \
 --metrics-server=true \
 --metrics-server-address=0.0.0.0 \
 --metrics-server-port=8008 \
 --staticnode=/ip4/172.17.0.2/tcp/60000/p2p/16Uiu2...
```
