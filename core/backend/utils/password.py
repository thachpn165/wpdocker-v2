from password_generator import PasswordGenerator

pwo = PasswordGenerator()
pwo.minlen = 20
pwo.maxlen = 20
pwo.digits = True
pwo.uppercase = True
pwo.specialchars = False

def strong_password():
    return pwo.generate()