# Day 20 — Kubernetes AI Inference Autoscaling Guard

This project validates GPU inference capacity controls before GitOps merge: demand-aware metrics, GPU requests/limits, probes, replica bounds, stabilization, cooldown, and fallback capacity.

Deploy read-only first, baseline existing workloads, protect SLO/policy changes, validate metric outages and cold starts, and retain reports. AI is advisory only and cannot change SLOs, capacity, merge approval, or deployment.

Interview story: explain why CPU is often a weak inference-demand signal, how readiness and stabilization affect cold starts, how fallback protects metric outages, and how latency, GPU utilization, idle cost, and false positives measure value.

Repository: https://github.com/ohjeffkuston/kubernetes-inference-autoscaling-guard
