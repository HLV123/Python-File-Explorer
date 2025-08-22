class FileExplorerError(Exception):
    pass


class PathAccessError(FileExplorerError):
    pass


class FileOperationError(FileExplorerError):
    pass


class InvalidPathError(FileExplorerError):
    pass


class PermissionDeniedError(FileExplorerError):
    pass


class ItemNotFoundError(FileExplorerError):
    pass