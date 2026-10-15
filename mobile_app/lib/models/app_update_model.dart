/// Trusted update manifest returned by `GET /api/app-updates/check/`.
///
/// The server is the source of truth: `updateAvailable` and
/// `mandatoryUpdate` are computed there (from the latest active release
/// and its minimum supported build) so a tampered client cannot silently
/// skip a mandatory update.
class AppUpdateInfo {
  final String platform;
  final int? currentBuildNumber;
  final bool updateAvailable;
  final bool mandatoryUpdate;
  final String? latestVersion;
  final int? latestBuildNumber;
  final String? minimumSupportedVersion;
  final String? releaseNotes;
  final String? downloadUrl;
  final String? checksumSha256;
  final DateTime? releasedAt;
  final String? message;

  AppUpdateInfo({
    this.platform = 'android',
    this.currentBuildNumber,
    this.updateAvailable = false,
    this.mandatoryUpdate = false,
    this.latestVersion,
    this.latestBuildNumber,
    this.minimumSupportedVersion,
    this.releaseNotes,
    this.downloadUrl,
    this.checksumSha256,
    this.releasedAt,
    this.message,
  });

  factory AppUpdateInfo.fromJson(Map<String, dynamic> json) {
    return AppUpdateInfo(
      platform: json['platform'] as String? ?? 'android',
      currentBuildNumber: json['current_build_number'] as int?,
      updateAvailable: json['update_available'] as bool? ?? false,
      mandatoryUpdate: json['mandatory_update'] as bool? ?? false,
      latestVersion: json['latest_version'] as String?,
      latestBuildNumber: json['latest_build_number'] as int?,
      minimumSupportedVersion: json['minimum_supported_version'] as String?,
      releaseNotes: json['release_notes'] as String?,
      downloadUrl: json['download_url'] as String?,
      checksumSha256: json['checksum_sha256'] as String?,
      releasedAt: json['released_at'] == null
          ? null
          : DateTime.tryParse(json['released_at'] as String),
      message: json['message'] as String?,
    );
  }

  /// No release published on the server (or server used an unexpected shape).
  bool get isUnknown => latestVersion == null && message != null;
}
