from password_generator import PasswordGenerator
from core.backend.utils.debug import log_call



pwo = PasswordGenerator()
pwo.minlen = 16
pwo.maxlen = 26
pwo.minnumbers = 2
pwo.minschars = 3
pwo.excludeschars = "!$%^&*()_+<>?:{}[]|.,;~`#@'"

@log_call
def strong_password():
    return pwo.generate()