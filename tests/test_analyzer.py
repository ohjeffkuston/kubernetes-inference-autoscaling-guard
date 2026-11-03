from pathlib import Path

from inference_autoscaling_guard.analyzer import analyze_documents, load_documents

SAMPLE = Path(__file__).parents[1] / "samples" / "compliant-hpa.yaml"


def docs():
    return load_documents([SAMPLE])


def test_compliant_hpa_passes():
    report = analyze_documents(docs())
    assert report.decision == "PASS"
    assert report.score == 100


def test_missing_autoscaler_blocks():
    assert analyze_documents(docs()[:1]).findings[-1].rule_id == "AS005"


def test_missing_gpu_request_blocks():
    data = docs()
    del data[0]["spec"]["template"]["spec"]["containers"][0]["resources"]["requests"]["nvidia.com/gpu"]
    assert any(item.rule_id == "AS002" for item in analyze_documents(data).findings)


def test_gpu_request_limit_mismatch_blocks():
    data = docs()
    data[0]["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["nvidia.com/gpu"] = 2
    assert any(item.rule_id == "AS003" for item in analyze_documents(data).findings)


def test_missing_probes_reviews():
    data = docs()
    del data[0]["spec"]["template"]["spec"]["containers"][0]["startupProbe"]
    assert any(item.rule_id == "AS004" for item in analyze_documents(data).findings)


def test_hpa_v1_blocks():
    data = docs()
    data[1]["apiVersion"] = "autoscaling/v1"
    assert any(item.rule_id == "AS006" for item in analyze_documents(data).findings)


def test_invalid_capacity_range_blocks():
    data = docs()
    data[1]["spec"]["maxReplicas"] = 2
    assert any(item.rule_id == "AS007" for item in analyze_documents(data).findings)


def test_cpu_only_metric_reviews():
    data = docs()
    data[1]["spec"]["metrics"] = [{"type": "Resource", "resource": {"name": "cpu", "target": {"type": "Utilization", "averageUtilization": 70}}}]
    assert any(item.rule_id == "AS008" for item in analyze_documents(data).findings)


def test_short_stabilization_reviews():
    data = docs()
    data[1]["spec"]["behavior"]["scaleDown"]["stabilizationWindowSeconds"] = 60
    assert any(item.rule_id == "AS009" for item in analyze_documents(data).findings)


def test_missing_slo_reviews():
    data = docs()
    del data[0]["spec"]["template"]["metadata"]["annotations"]
    assert any(item.rule_id == "AS001" for item in analyze_documents(data).findings)
