from rest_framework import serializers

from .models import FoodScan, MealEntry, MealItem


class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = [
            "id",
            "name",
            "quantity",
            "unit",
            "grams",
            "kcal",
            "protein_g",
            "carbs_g",
            "fat_g",
            "fiber_g",
            "confidence",
            "was_edited",
        ]


class MealEntrySerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True, read_only=True)
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = MealEntry
        fields = [
            "id",
            "member",
            "member_name",
            "scan",
            "eaten_on",
            "meal_type",
            "source",
            "total_kcal",
            "protein_g",
            "carbs_g",
            "fat_g",
            "fiber_g",
            "created_at",
            "items",
        ]
        read_only_fields = ["total_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g", "created_at", "source"]


class MealItemInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    quantity = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    unit = serializers.CharField(max_length=20, default="serving")
    grams = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    kcal = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    protein_g = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0, default=0)
    carbs_g = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0, default=0)
    fat_g = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0, default=0)
    fiber_g = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0, default=0)
    confidence = serializers.CharField(max_length=10, required=False, allow_blank=True)
    was_edited = serializers.BooleanField(default=False)


class ConfirmScanSerializer(serializers.Serializer):
    eaten_on = serializers.DateField()
    meal_type = serializers.ChoiceField(choices=MealEntry.MealType.choices)
    items = MealItemInputSerializer(many=True, min_length=1)
    edited = serializers.BooleanField(default=False)


class ManualMealSerializer(serializers.Serializer):
    member = serializers.IntegerField(required=False)
    eaten_on = serializers.DateField()
    meal_type = serializers.ChoiceField(choices=MealEntry.MealType.choices)
    items = MealItemInputSerializer(many=True, min_length=1)


class FoodScanSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.full_name", read_only=True)

    class Meta:
        model = FoodScan
        fields = [
            "id",
            "member",
            "member_name",
            "meal_type",
            "note",
            "status",
            "analysis",
            "error",
            "latency_ms",
            "model_name",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields
