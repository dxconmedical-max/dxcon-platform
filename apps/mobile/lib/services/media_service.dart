/// Camera and gallery media service foundation.
class MediaService {
  static const maxFileSizeBytes = 10 * 1024 * 1024; // 10 MB
  static const allowedMimeTypes = {'image/jpeg', 'image/png', 'image/webp'};

  bool validateFileSize(int bytes) => bytes <= maxFileSizeBytes;

  bool validateMimeType(String mime) => allowedMimeTypes.contains(mime);
}
