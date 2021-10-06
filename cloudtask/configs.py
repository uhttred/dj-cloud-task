from django.conf import settings

DCT_SECRET_HEADER_NAME: str = 'X-DCT-SECRET' 
DEFAULTS: dict = {
    'URL': None, # Default URL target to handle tasks,
    'SAE': None, # Service Account Email Used for HTTP authentication
    'SECRET': None, # Secreve key to validate incomes request
    'PROJECT': None, # Google Task Queue related project id
    'LOCATION': None # Google Task Queue Location
}

class CloudTaskSettings:

    __defaults: dict

    def __init__(self, defaults: dict = None, user_settings: dict = None) -> None:
        if user_settings:
            self.__settings = user_settings
        self.__defaults = defaults or DEFAULTS

    @property
    def settigs(self) -> dict:
        if not hasattr(self, '__settings'):
            return getattr(settings, 'CLOUDTASK', {})
        return self.__settings

    def __getattr__(self, attr: str):

        if attr not in self.__defaults:
            raise AttributeError("Invalid CLOUDTASK setting: '%s'" % attr)
        
        try:
            value = self.settigs[attr]
        except KeyError:
            value = self.__defaults[attr]

        setattr(self, attr, value)
        return value


conf = CloudTaskSettings()
