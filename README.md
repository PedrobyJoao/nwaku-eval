Performance evaluation testing of [NWaku relay nodes](https://github.com/waku-org/nwaku)

What is being evaluated:

1. How the **number** of messages affects bandwidth and delay.
2. How the **size** of messages affects bandwidth and delay.
3. How the **rate** of messages affects bandwidth and delay.

## Executing experiments

TODO with UV

## How

1. Create a mesh of nodes using docker network and containers
2. from where do I get the info? metrics or logs?

## Future improvements

TODO

## Final considerations

Is it effective to evaluate performance deploying several nodes on the same machine at all?
They'll be sharing the same network namespace, same hardware resources...

TODO

## TODOs

- Check if PX discovery is fast enough to interconnect peers within the mesh
- move `black` to `uv` pyproject def
- is `uv` and its pyproject correctly being used? (package vs library...)
- mesh in-file TODOs
- review project structure
