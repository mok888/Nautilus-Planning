class BuilderError(RuntimeError):
    pass

class CriticalFieldError(BuilderError):
    pass

class CodegenFailure(BuilderError):
    pass

class SnapshotMismatch(BuilderError):
    pass

class CargoCheckError(BuilderError):
    pass
