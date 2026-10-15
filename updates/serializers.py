from rest_framework import serializers

from .models import AppRelease


class AppReleaseSerializer(serializers.ModelSerializer):
    """Used by ShopZen admins to publish new builds."""

    class Meta:
        model = AppRelease
        fields = [
            'id', 'platform', 'version_name', 'version_code',
            'minimum_supported_code', 'minimum_supported_name',
            'release_notes', 'download_url',
            'checksum_sha256', 'is_active', 'released_at',
        ]
        read_only_fields = ['id', 'released_at']

    def validate_version_code(self, value):
        if value < 1:
            raise serializers.ValidationError('Version code must be a positive build number.')
        return value

    def validate(self, attrs):
        code = attrs.get('version_code', getattr(self.instance, 'version_code', None))
        minimum = attrs.get('minimum_supported_code', getattr(self.instance, 'minimum_supported_code', 1))
        if minimum > code:
            raise serializers.ValidationError({
                'minimum_supported_code': 'Minimum supported build cannot exceed the release build number.'
            })
        return attrs


class AppUpdateManifestSerializer(serializers.ModelSerializer):
    """The trusted manifest returned to clients on update check."""

    latest_version = serializers.CharField(source='version_name')
    latest_build_number = serializers.IntegerField(source='version_code')
    minimum_supported_version = serializers.CharField(source='minimum_supported_name')
    mandatory_update = serializers.SerializerMethodField()

    class Meta:
        model = AppRelease
        fields = [
            'latest_version', 'latest_build_number', 'minimum_supported_version',
            'release_notes', 'download_url', 'checksum_sha256',
            'mandatory_update', 'released_at',
        ]

    def get_mandatory_update(self, obj):
        current_code = self.context.get('current_code', 0)
        return current_code < obj.minimum_supported_code
