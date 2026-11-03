# Deployment and operations

## Safe rollout

1. Run the guard read-only against changed manifests in pull requests.
2. Begin with `REVIEW` non-blocking while baselining existing workloads.
3. Protect the policy file and SLO annotations with code owners.
4. Validate metric availability, startup duration, model-loading behavior, and maximum GPU quota in staging.
5. Promote deterministic `BLOCK` findings to a required check only after false-positive review.
6. Retain JSON reports and autoscaler events for audits and tuning.

```bash
python -m pip install -e .
inference-autoscaling-guard samples/compliant-hpa.yaml --output json
```

## Security and reliability boundaries

- The tool never calls Kubernetes or a cloud provider and never changes replica counts.
- AI output is untrusted advisory text and cannot alter SLOs, capacity limits, policy, merge approval, or deployment.
- Custom metrics can fail or lag; test metric-outage behavior and KEDA fallback capacity.
- GPU quota, node provisioning time, image pull, and model load can dominate scale-up latency.
- A passing manifest proves policy coverage, not that the production metric pipeline is correct.

## Measures

- p95/p99 inference latency and SLO attainment.
- Queue age and backlog per ready replica.
- Scale-up time and cold-start duration.
- GPU utilization and idle-GPU minutes.
- Cost per successful inference.
- Replica-flap rate, metric failures, and fallback activations.
- Change-failure rate and autoscaling-policy false positives.
