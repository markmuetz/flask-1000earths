import secret_settings

SITE = 'site'
CACHE = 'cache'

if hasattr(secret_settings, 'USE_GIT'):
    USE_GIT = secret_settings.USE_GIT
else:
    USE_GIT = True
