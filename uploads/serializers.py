from rest_framework import serializers
from .models import Entities, Sprints, History

class EntitiesSerializer(serializers.ModelSerializer):
    # spent = serializers.IntegerField(required=False)

    # def validate_spent(self, value):
    #     if str(value).isdigit():
    #         return int(value)
    #     return 0

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    class Meta:
        model = Entities
        fields = [
            'entity_id', 'area', 'type', 'status', 'state', 'priority', 'ticket_number', 'name',
            'create_date', 'created_by', 'update_date', 'updated_by', 'parent_ticket_id',
            'assignee', 'owner', 'due_date', 'rank', 'estimation', 'spent', 'workgroup', 'resolutio'
        ]


class SprintsSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)
    
    class Meta:
        model = Sprints
        fields = [
            'sprint_name', 'sprint_status', 'sprint_start_date', 'sprint_end_date', 'ticket_number'
        ]


class HistorySerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)
    
    class Meta:
        model = History
        fields = [
            'entity_id', 'history_property_name', 'history_date', 'history_version',
            'history_change_type', 'history_change'
        ]
