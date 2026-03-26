class RecognitionError(Exception):
    pass


class RecognitionConfigurationError(RecognitionError):
    pass


class RecognitionDependencyError(RecognitionError):
    pass

