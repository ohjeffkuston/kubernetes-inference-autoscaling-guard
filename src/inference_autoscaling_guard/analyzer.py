"""Deterministic analysis of AI inference workload and autoscaler manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    resource: str
    message: str
    remediation: str


@dataclass(frozen=True)
class AnalysisReport:
    decision: str
    score: int
    workloads_checked: int
    findings: tuple[Finding, ...]
    advisory_ai_prompt: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "score": self.score,
            "workloads_checked": self.workloads_checked,
            "findings": [asdict(item) for item in self.findings],
            "advisory_ai_prompt": self.advisory_ai_prompt,
        }


def load_documents(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        candidates = sorted(path.rglob("*.y*ml")) if path.is_dir() else [path]
        for candidate in candidates:
            with candidate.open("r", encoding="utf-8") as handle:
                documents.extend(doc for doc in yaml.safe_load_all(handle) if isinstance(doc, dict))
    return documents


def _id(document: dict[str, Any]) -> str:
    metadata = document.get("metadata") or {}
    return f"{document.get('kind', 'Unknown')}/{metadata.get('namespace', 'default')}/{metadata.get('name', 'unnamed')}"


def _finding(rule: str, severity: str, resource: str, message: str, remediation: str) -> Finding:
    return Finding(rule, severity, resource, message, remediation)


def _workload_key(document: dict[str, Any]) -> tuple[str, str]:
    metadata = document.get("metadata") or {}
    return metadata.get("namespace", "default"), metadata.get("name", "unnamed")


def _metric_names(hpa: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for metric in (hpa.get("spec") or {}).get("metrics") or []:
        metric_type = metric.get("type", "")
        section = metric.get(metric_type.lower()) or metric.get(metric_type) or {}
        metric_ref = section.get("metric") or {}
        names.append(str(metric_ref.get("name") or metric.get("resource", {}).get("name") or "").lower())
    return names


def analyze_documents(documents: list[dict[str, Any]]) -> AnalysisReport:
    workloads: dict[tuple[str, str], dict[str, Any]] = {}
    hpas: dict[tuple[str, str], dict[str, Any]] = {}
    scaled_objects: dict[tuple[str, str], dict[str, Any]] = {}

    for document in documents:
        kind = document.get("kind")
        namespace = (document.get("metadata") or {}).get("namespace", "default")
        spec = document.get("spec") or {}
        if kind == "Deployment":
            labels = (((spec.get("template") or {}).get("metadata") or {}).get("labels") or {})
            if labels.get("platform.example.com/workload-class") == "ai-inference":
                workloads[_workload_key(document)] = document
        elif kind == "HorizontalPodAutoscaler":
            target = spec.get("scaleTargetRef") or {}
            hpas[(namespace, target.get("name", ""))] = document
        elif kind == "ScaledObject":
            target = spec.get("scaleTargetRef") or {}
            scaled_objects[(namespace, target.get("name", ""))] = document

    findings: list[Finding] = []
    for key, workload in workloads.items():
        resource = _id(workload)
        template = ((workload.get("spec") or {}).get("template") or {})
        metadata = template.get("metadata") or {}
        pod_spec = template.get("spec") or {}
        annotations = metadata.get("annotations") or {}
        containers = pod_spec.get("containers") or []

        if not annotations.get("slo.platform.example.com/p95-latency-ms"):
            findings.append(_finding("AS001", "REVIEW", resource, "No p95 latency objective is declared.", "Declare the latency objective used to validate scaling behavior."))

        for container in containers:
            resources = container.get("resources") or {}
            requests = resources.get("requests") or {}
            limits = resources.get("limits") or {}
            requested_gpu = requests.get("nvidia.com/gpu")
            limited_gpu = limits.get("nvidia.com/gpu")
            if requested_gpu is None:
                findings.append(_finding("AS002", "BLOCK", resource, f"Container {container.get('name', 'unnamed')!r} has no GPU request.", "Declare nvidia.com/gpu in requests and limits."))
            elif requested_gpu != limited_gpu:
                findings.append(_finding("AS003", "BLOCK", resource, "GPU request and limit do not match.", "Use equal integer GPU requests and limits for deterministic scheduling."))
            if not container.get("startupProbe") or not container.get("readinessProbe"):
                findings.append(_finding("AS004", "REVIEW", resource, "Startup or readiness probe is missing.", "Keep cold-starting replicas out of service and autoscaling metrics until ready."))

        hpa = hpas.get(key)
        scaled = scaled_objects.get(key)
        if not hpa and not scaled:
            findings.append(_finding("AS005", "BLOCK", resource, "No HPA or KEDA ScaledObject targets this inference workload.", "Add an autoscaler using queue, concurrency, or latency-aware metrics."))
            continue

        if hpa:
            hpa_resource = _id(hpa)
            spec = hpa.get("spec") or {}
            if hpa.get("apiVersion") != "autoscaling/v2":
                findings.append(_finding("AS006", "BLOCK", hpa_resource, "HPA does not use autoscaling/v2.", "Use autoscaling/v2 for custom/external metrics and behavior controls."))
            if int(spec.get("maxReplicas", 0)) <= int(spec.get("minReplicas", 1)):
                findings.append(_finding("AS007", "BLOCK", hpa_resource, "maxReplicas must exceed minReplicas.", "Set a tested capacity range with headroom."))
            metric_names = _metric_names(hpa)
            if not any(any(token in name for token in ("queue", "concurrency", "request", "latency")) for name in metric_names):
                findings.append(_finding("AS008", "REVIEW", hpa_resource, "Autoscaling is not driven by a demand or latency metric.", "Add queue depth, concurrency, request rate, or latency-aware custom metrics."))
            behavior = spec.get("behavior") or {}
            scale_down = behavior.get("scaleDown") or {}
            if int(scale_down.get("stabilizationWindowSeconds", 0)) < 300:
                findings.append(_finding("AS009", "REVIEW", hpa_resource, "Scale-down stabilization is below 300 seconds.", "Use a stabilization window that prevents GPU replica flapping."))

        if scaled:
            scaled_resource = _id(scaled)
            spec = scaled.get("spec") or {}
            if int(spec.get("maxReplicaCount", 0)) <= int(spec.get("minReplicaCount", 0)):
                findings.append(_finding("AS010", "BLOCK", scaled_resource, "maxReplicaCount must exceed minReplicaCount.", "Set a tested capacity range with headroom."))
            if int(spec.get("cooldownPeriod", 0)) < 300:
                findings.append(_finding("AS011", "REVIEW", scaled_resource, "KEDA cooldown is below 300 seconds.", "Use a cooldown that accounts for model load time and avoids churn."))
            if not spec.get("fallback"):
                findings.append(_finding("AS012", "REVIEW", scaled_resource, "KEDA metric-source fallback capacity is missing.", "Configure failureThreshold and fallback replicas for metric outages."))
            trigger_types = {str(item.get("type", "")).lower() for item in spec.get("triggers") or []}
            if not trigger_types or trigger_types.issubset({"cpu", "memory"}):
                findings.append(_finding("AS013", "REVIEW", scaled_resource, "KEDA triggers are absent or resource-only.", "Use queue, Prometheus, or another workload-demand trigger."))

    blocks = sum(item.severity == "BLOCK" for item in findings)
    reviews = sum(item.severity == "REVIEW" for item in findings)
    decision = "BLOCK" if blocks else "REVIEW" if reviews else "PASS"
    score = max(0, 100 - blocks * 25 - reviews * 8)
    prompt = (
        "Explain the deterministic autoscaling findings and draft a minimal manifest patch. "
        "Do not change SLOs, capacity limits, production replicas, approve a merge, or deploy."
    )
    return AnalysisReport(decision, score, len(workloads), tuple(findings), prompt)
