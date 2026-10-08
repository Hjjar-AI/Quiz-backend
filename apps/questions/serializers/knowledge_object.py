from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import KnowledgeObject, Tag, clean_tag_name
from ..knowledge_validation import normalize_knowledge_translations


class KnowledgeObjectSerializer(serializers.ModelSerializer):
    source_page = serializers.IntegerField(min_value=1, required=False, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True,
    )
    created_by_username = serializers.CharField(
        source='created_by.username', read_only=True, default=None,
    )
    question_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = KnowledgeObject
        fields = [
            'id', 'uuid', 'title', 'learning_objective', 'canonical_answer',
            'key_facts', 'misconceptions', 'category', 'category_name',
            'tags', 'tag_names', 'source_document', 'source_page',
            'translations', 'status', 'version', 'last_revised_at',
            'created_by', 'created_by_username', 'question_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'uuid', 'version', 'created_by', 'created_by_username',
            'question_count', 'created_at', 'updated_at',
        ]

    def _validate_string_list(self, value, label):
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise serializers.ValidationError(f'{label} must be a list of text values.')
        return [item.strip() for item in value if item.strip()]

    def validate_key_facts(self, value):
        return self._validate_string_list(value, 'key_facts')

    def validate_misconceptions(self, value):
        return self._validate_string_list(value, 'misconceptions')

    def validate_translations(self, value):
        try:
            return normalize_knowledge_translations(value)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc

    def _set_tags(self, instance, names):
        if names is None:
            return
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(name=clean_tag_name(name))
            tags.append(tag)
        instance.tags.set(tags)

    @transaction.atomic
    def create(self, validated_data):
        names = validated_data.pop('tag_names', None)
        instance = super().create(validated_data)
        self._set_tags(instance, names)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        # DRF may have fetched this instance before another editor committed.
        # Apply a partial update to current state, preserving unrelated edits.
        instance = KnowledgeObject.objects.select_for_update().get(pk=instance.pk)
        names = validated_data.pop('tag_names', None)
        validated_data['version'] = instance.version + 1
        instance = super().update(instance, validated_data)
        self._set_tags(instance, names)
        return instance
