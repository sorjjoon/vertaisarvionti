from __future__ import annotations

import pytz

class AuthError(Exception):
    pass

class AccountLockedError(AuthError):
    def __init__(self, message, locked_until, timezone="utc"):
        
        super().__init__(message)
        self.locked_until = pytz.timezone(timezone).localize(locked_until)







class FileErrpr(Exception):
    pass

class LargeFileError(AuthError):
    def __init__(self, message, filename, max_size="50 MB"):
        
        super().__init__(message)
        self.filename=filename