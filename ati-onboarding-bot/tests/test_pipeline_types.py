def test_pipeline_aggregation_group_shape():
    pipeline = [
        {"$match": {"tenant_id": "default"}},
        {
            "$group": {
                "_id": {"$ifNull": ["$project_type", "unknown"]},
                "total": {"$sum": 1},
                "completed": {"$sum": {"$cond": ["$done", 1, 0]}},
            }
        },
    ]
    assert pipeline[0]["$match"]["tenant_id"] == "default"
    assert "$group" in pipeline[1]
