from password_generator import PasswordGenerator
from core.backend.utils.debug import log_call



pwo = PasswordGenerator()
pwo.minlen = 20
pwo.maxlen = 20
pwo.digits = True
pwo.uppercase = True
pwo.specialchars = False

@log_call
def strong_password():
    return pwo.generate()