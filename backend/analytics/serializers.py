from rest_framework import serializers

from . import metrics

GRANULARITIES = {"day", "week", "month"}


def _clamp(value, lo, hi, default):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


class BlockPlanSerializer(serializers.Serializer):
    metric = serializers.ChoiceField(choices=list(metrics.REGISTRY))
    viz = serializers.CharField(required=False, allow_blank=True, default="")
    params = serializers.DictField(required=False, default=dict)

    def validate(self, attrs):
        spec = metrics.REGISTRY[attrs["metric"]]
        raw = attrs.get("params") or {}

        days = raw.get("period_days")
        if days is None and raw.get("period_months") is not None:
            days = _clamp(raw.get("period_months"), 1, 13, 1) * 30
        clean = {"period_days": _clamp(days, 1, 400, 30)}
        if "limit" in spec["params"]:
            clean["limit"] = _clamp(raw.get("limit", 10), 1, 50, 10)
        if "granularity" in spec["params"]:
            gran = raw.get("granularity")
            clean["granularity"] = gran if gran in GRANULARITIES else "week"

        viz = attrs.get("viz") or spec["default_viz"]
        attrs["viz"] = viz if viz in spec["allowed_viz"] else spec["default_viz"]
        attrs["params"] = clean
        return attrs


class PlanSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, default="")
    insight_kind = serializers.ChoiceField(
        choices=["template", "llm"], required=False, default="template"
    )
    unsupported = serializers.BooleanField(required=False, default=False)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    blocks = BlockPlanSerializer(many=True)

    def validate_blocks(self, value):
        if not value:
            raise serializers.ValidationError("Plan harus punya minimal satu block.")
        return value[:4]


class QuerySerializer(serializers.Serializer):
    question = serializers.CharField(required=False, allow_blank=True, max_length=300)
    preset = serializers.CharField(required=False, allow_blank=True)
