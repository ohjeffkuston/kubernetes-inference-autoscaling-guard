# Demand validation

Checked: 2026-11-03 (America/Detroit)

## Why this project

Production AI inference needs capacity controls that react to actual demand without creating GPU churn, cold-start latency, or unsafe scale-down. Current AI-platform roles repeatedly combine Kubernetes, GPU scheduling, autoscaling, observability, and operational reliability.

Live postings reviewed:

- AI/ML infrastructure platform role: U.S. remote, Kubernetes GPU workloads, $120K–$250K; citizenship/clearance restriction makes it unsuitable for application but validates the technical demand. https://job-boards.greenhouse.io/openteams/jobs/4735509005
- AI infrastructure Kubernetes role: remote U.S., GPU training/inference infrastructure, $180K–$250K. https://jobs.ashbyhq.com/fal-ai/d9384b0a-2f86-4e9a-bcc7-5b49f1c0b081/
- AI/ML platform role: remote U.S., Kubernetes, Terraform, GPU/HPC infrastructure, $136K–$240K base. https://jobs.ashbyhq.com/deepgram/f424ef6a-c27f-4984-9e77-40a1ad16ae28
- AI platform role: U.S. remote, enterprise AI infrastructure and evaluation tooling. https://job-boards.greenhouse.io/lts/jobs/4337509009

These postings validate the problem domain, not candidate fit or application eligibility.

## Authoritative sources

- Kubernetes HPA: custom/external metrics, readiness behavior, multiple metrics, and stabilization windows. https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/
- Kubernetes autoscaling/v2 API: scaling policies, stabilization, and tolerance. https://kubernetes.io/docs/reference/kubernetes-api/autoscaling/horizontal-pod-autoscaler-v2/
- KEDA ScaledObject: cooldown, trigger polling, and metric-source fallback capacity. https://keda.sh/docs/2.21/reference/scaledobject-spec/
- Kubernetes v1.37 HPA scale-to-zero: queue-driven external metrics and downscale stabilization. https://kubernetes.io/blog/2026/09/02/kubernetes-v1-37-hpa-scale-to-zero-beta/

## Design conclusion

The guard evaluates only reviewable GitOps evidence. It does not choose production capacity or mutate a cluster. AI may explain findings or draft a patch, while deterministic policy and human approval retain authority.
