WRN 2025-07-09 14:00:05.989+00:00 whether to mount storeSync is not specified, defaulting to not mounting topics="waku conf builder" tid=1 file=waku_conf_builder.nim:425
WRN 2025-07-09 14:00:05.989+00:00 missing node key, generating new set topics="waku conf builder" tid=1 file=waku_conf_builder.nim:284
bSubscribeShards: none(seq[uint16])
INF 2025-07-09 14:00:05.989+00:00 Sharding configuration: topics="waku conf builder" tid=1 file=waku_conf_builder.nim:453 shardingConf="(kind: AutoSharding, numShardsInCluster: 1)" subscribeShards=@[0]
INF 2025-07-09 14:00:05.989+00:00 Configuration: Enabled protocols topics="waku conf" tid=1 file=waku_conf.nim:142 relay=true rlnRelay=false store=false filter=false lightPush=false peerExchange=true
INF 2025-07-09 14:00:05.989+00:00 Configuration. Network topics="waku conf" tid=1 file=waku_conf.nim:150 cluster=0
INF 2025-07-09 14:00:05.989+00:00 Configuration. Active Relay Shards topics="waku conf" tid=1 file=waku_conf.nim:153 shard=0
NTC 2025-07-09 14:00:05.989+00:00 REST service started tid=1 file=server.nim:186 address=0.0.0.0:42145
INF 2025-07-09 14:00:05.989+00:00 Starting REST HTTP server tid=1 file=builder.nim:112 url=http://0.0.0.0:42145/
INF 2025-07-09 14:00:09.997+00:00 Initializing networking tid=1 file=waku_node.nim:136 addrs=@[/ip4/127.0.0.1/tcp/60000]
INF 2025-07-09 14:00:09.997+00:00 Created WakuMetadata protocol topics="waku node" tid=1 file=protocol.nim:125 clusterId=0 shards={0}
INF 2025-07-09 14:00:09.997+00:00 mounting store client topics="waku node" tid=1 file=waku_node.nim:980
INF 2025-07-09 14:00:09.997+00:00 mounting legacy store client topics="waku node" tid=1 file=waku_node.nim:847
INF 2025-07-09 14:00:09.997+00:00 mounting auto sharding topics="waku node" tid=1 file=waku_node.nim:205 clusterId=0 shardCount=1
INF 2025-07-09 14:00:09.997+00:00 mounting relay protocol topics="waku node" tid=1 file=waku_node.nim:452
INF 2025-07-09 14:00:09.998+00:00 relay mounted successfully topics="waku node" tid=1 file=waku_node.nim:469
INF 2025-07-09 14:00:09.998+00:00 mounting rendezvous discovery protocol topics="waku node" tid=1 file=waku_node.nim:1416
ERR 2025-07-09 14:00:09.998+00:00 rendezvous failed initial requests topics="waku node" tid=1 file=waku_node.nim:1424 error="could not get a peer supporting RendezVousCodec"
INF 2025-07-09 14:00:09.998+00:00 mounting libp2p ping protocol topics="waku node" tid=1 file=waku_node.nim:1341
INF 2025-07-09 14:00:09.998+00:00 mounting light push client topics="waku node" tid=1 file=waku_node.nim:1156
INF 2025-07-09 14:00:09.998+00:00 mounting legacy light push client topics="waku node" tid=1 file=waku_node.nim:1040
INF 2025-07-09 14:00:09.998+00:00 mounting filter client topics="waku node" tid=1 file=waku_node.nim:518
INF 2025-07-09 14:00:09.998+00:00 mounting waku peer exchange topics="waku node" tid=1 file=waku_node.nim:1260
INF 2025-07-09 14:00:09.998+00:00 No external callbacks to be set topics="wakunode waku" tid=1 file=waku.nim:123
INF 2025-07-09 14:00:09.998+00:00 Running nwaku node tid=1 file=node_factory.nim:435 version=v0.35.1-114-ga0f8cb
INF 2025-07-09 14:00:09.998+00:00 Starting Waku node topics="waku node" tid=1 file=waku_node.nim:1482 version=v0.35.1-114-ga0f8cb
INF 2025-07-09 14:00:09.998+00:00 starting relay protocol topics="waku node" tid=1 file=waku_node.nim:419
INF 2025-07-09 14:00:09.998+00:00 relay started successfully topics="waku node" tid=1 file=waku_node.nim:440
INF 2025-07-09 14:00:09.999+00:00 Setting up AutonatService topics="libp2p autonatservice" tid=1 file=service.nim:213
WRN 2025-07-09 14:00:09.999+00:00 Starting gossipsub twice topics="libp2p gossipsub" tid=1 file=gossipsub.nim:858
INF 2025-07-09 14:00:09.999+00:00 PeerInfo topics="waku node" tid=1 file=waku_node.nim:1447 peerId=16U*q9UHRD addrs=@[/ip4/127.0.0.1/tcp/60000]
INF 2025-07-09 14:00:09.999+00:00 Listening on topics="waku node" tid=1 file=waku_node.nim:1470 full=[/ip4/0.0.0.0/tcp/60000/p2p/16Uiu2HAm39z2qCkyeGxfNdxf13RfAKDG5i1rezorxevqzrq9UHRD] localIp=172.19.0.4 switchAddress=@[/ip4/172.19.0.4/tcp/60000]
INF 2025-07-09 14:00:09.999+00:00 Announcing addresses topics="waku node" tid=1 file=waku_node.nim:1472 full=[/ip4/172.19.0.4/tcp/60000/p2p/16Uiu2HAm39z2qCkyeGxfNdxf13RfAKDG5i1rezorxevqzrq9UHRD]
INF 2025-07-09 14:00:10.000+00:00 DNS: discoverable ENR topics="waku node" tid=1 file=waku_node.nim:1473 enr=enr:-KC4QL2SKBBmzfVPTRRsWwsyHYwOeShAgD89NZm3TudDj3idfSbxQoRzz3uYZE45UJOlv23byHtZJe_lkK86X8MaLjMBgmlkgnY0gmlwhAAAAACKbXVsdGlhZGRyc4CCcnOFAAABAACJc2VjcDI1NmsxoQJy2J1G64huIPLN7WZeiQUWhdH_l7j_WmeKKIz7YApHNIN0Y3CC6mCFd2FrdTIB
INF 2025-07-09 14:00:10.000+00:00 Node started successfully topics="waku node" tid=1 file=waku_node.nim:1527
INF 2025-07-09 14:00:10.000+00:00 Dialing multiple peers tid=1 file=peer_manager.nim:345 numOfPeers=1 nodes="@[\"/ip4/172.19.0.2/tcp/60000/p2p/16Uiu2HAmLXbwczgHn5D1e2ta7KPrXTsfjTSp8nq8qKWdPrUMRv1s\"]"
INF 2025-07-09 14:00:10.012+00:00 Finished dialing multiple peers tid=1 file=peer_manager.nim:372 successfulConns=1 attempted=1
INF 2025-07-09 14:00:15.013+00:00 Relay peer connections topics="waku node peer_manager" tid=1 file=peer_manager.nim:765 inRelayConns=0/20 outRelayConns=1/10 totalConnections=1/50 notConnectedPeers=0 outsideBackoffPeers=0
INF 2025-07-09 14:00:15.014+00:00 PeerInfo topics="waku node" tid=1 file=waku_node.nim:1447 peerId=16U*q9UHRD addrs=@[/ip4/172.19.0.4/tcp/60000]
INF 2025-07-09 14:00:15.014+00:00 Listening on topics="waku node" tid=1 file=waku_node.nim:1470 full=[/ip4/0.0.0.0/tcp/60000/p2p/16Uiu2HAm39z2qCkyeGxfNdxf13RfAKDG5i1rezorxevqzrq9UHRD] localIp=172.19.0.4 switchAddress=@[/ip4/172.19.0.4/tcp/60000]
INF 2025-07-09 14:00:15.014+00:00 Announcing addresses topics="waku node" tid=1 file=waku_node.nim:1472 full=[/ip4/172.19.0.4/tcp/60000/p2p/16Uiu2HAm39z2qCkyeGxfNdxf13RfAKDG5i1rezorxevqzrq9UHRD]
INF 2025-07-09 14:00:15.014+00:00 DNS: discoverable ENR topics="waku node" tid=1 file=waku_node.nim:1473 enr=enr:-KC4QL2SKBBmzfVPTRRsWwsyHYwOeShAgD89NZm3TudDj3idfSbxQoRzz3uYZE45UJOlv23byHtZJe_lkK86X8MaLjMBgmlkgnY0gmlwhAAAAACKbXVsdGlhZGRyc4CCcnOFAAABAACJc2VjcDI1NmsxoQJy2J1G64huIPLN7WZeiQUWhdH_l7j_WmeKKIz7YApHNIN0Y3CC6mCFd2FrdTIB
INF 2025-07-09 14:00:15.015+00:00 starting keepalive tid=1 file=node_health_monitor.nim:369 randomPeersKeepalive=10s allPeersKeepalive=2m
INF 2025-07-09 14:00:15.019+00:00 REST services are installed tid=1 file=builder.nim:218
INF 2025-07-09 14:00:15.019+00:00 Starting metrics HTTP server topics="waku node metrics" tid=1 file=waku_metrics.nim:63 serverIp=0.0.0.0 serverPort=42979
INF 2025-07-09 14:00:15.019+00:00 Metrics HTTP server started topics="waku node metrics" tid=1 file=waku_metrics.nim:73 serverIp=0.0.0.0 serverPort=42979
INF 2025-07-09 14:00:15.019+00:00 Node setup complete topics="wakunode main" tid=1 file=wakunode2.nim:104
NTC 2025-07-09 14:00:36.506+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0xaae6584c50ab177634968bfa0077dd041808a86fd6ba27676556c935ad4bb880 msg_id=0ab649557c30...2365aa7f9ebc from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636506984960 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.512+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x2bd8fa79ba46b89e1c4bad2065bd701e18da73d2439e2f3f7216c8d9614c875e msg_id=17d8a86240d5...dafb9b6b7966 from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636512892160 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.518+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x6b0cdf29e93ed848436282a922a4c58fdbe7ea3a543f2732c005e8c2326dc3cd msg_id=9af0ea1b21eb...57fe24470d3f from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636519636992 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.525+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x56bb99da05eadf8c34e8cc145ad1bc01a6ad29fc10e356446814443d4c954e2d msg_id=94be8b49d74d...2f552de38d97 from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636526632960 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.530+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x98a7b3b481ad194e756869c1b6eafb140077e83d29252cb814be66e2e1593360 msg_id=2b079914518e...4ee55e4fc6e3 from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636531019520 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.533+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x53fe9e62784c63f429c5c9b0d0b2dbfba1a1ff3b2d1ab360675c796f34682774 msg_id=e79eeb217f4c...dd5dfadb8230 from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636534293760 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.536+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x06ee9f02fff95889960bf51ff52fc172e912353ba79f1dd6e8da55f0dcd60128 msg_id=29126f4db6f6...3e73ef76bc86 from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636536710400 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.538+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x92bd6e645feb2153395248f9904feb8e5d797ba20fa768c1a2d65e03deea6692 msg_id=3da2930eb33f...29b16922848a from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636539057152 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.540+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0x743aea9c3f3b95d6a9e7630c122912be47936fb7a8a514eed10d2c214e1e00f7 msg_id=03192cbbfa58...47c7b7ff617a from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636541252864 payloadSizeBytes=20
NTC 2025-07-09 14:00:36.542+00:00 received relay message topics="waku relay" tid=1 file=protocol.nim:181 my_peer_id=16U*q9UHRD msg_hash=0xbec9cb4ed0d40d652be3641e71639c9484b21de715b29e374204c25ad7bee02b msg_id=2d31f96563b1...e03d72641893 from_peer_id=16U*UMRv1s topic=waku/2/default-waku/proto receivedTime=1752069636543552256 payloadSizeBytes=20
INF 2025-07-09 14:01:15.014+00:00 Retrieving peer info via peer exchange protocol topics="waku node" tid=1 file=waku_node.nim:1288 amount=5
INF 2025-07-09 14:01:15.019+00:00 Retrieved peer info via peer exchange protocol topics="waku node" tid=1 file=waku_node.nim:1298 validPeers=0 totalPeers=0
INF 2025-07-09 14:01:40.008+00:00 Peer reachability status tid=1 file=autonat_service.nim:31 networkReachability=Reachable confidence=1.0
INF 2025-07-09 14:02:15.021+00:00 Retrieving peer info via peer exchange protocol topics="waku node" tid=1 file=waku_node.nim:1288 amount=5
INF 2025-07-09 14:02:15.025+00:00 Retrieved peer info via peer exchange protocol topics="waku node" tid=1 file=waku_node.nim:1298 validPeers=0 totalPeers=0
