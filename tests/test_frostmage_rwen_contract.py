from tools.analytics.frostmage_benchmark import FROST_CLUSTER
from tools.analytics.tactical_benchmark_suite import _validate_rwen


def test_frostmage_cluster_uses_canonical_rwen_shape():
    _validate_rwen(FROST_CLUSTER)
    rows = FROST_CLUSTER.split()[0].split("/")
    assert len(rows) == 8
    assert all(len(row.split(",")) == 8 for row in rows)
    assert all(cell == ".:." or not cell.startswith(".") for row in rows for cell in row.split(","))
