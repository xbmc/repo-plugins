# SPDX-License-Identifier: CC-BY-NC-SA-4.0


# noinspection PyClassHasNoInit
class Environments:

    """Enum class that holds the environments"""

    NoPlatform = 0
    Unknown = 1
    UWP = 2
    Linux = 4
    Windows = 8
    OSX = 16
    IOS = 64
    Android = 128
    TVOS = 256          # such as ATV4

    # special groups
    Apple = OSX | IOS | TVOS
    Google = Android
    All = UWP | Linux | Windows | OSX | IOS | Android | TVOS

    @staticmethod
    def name(environment):
        """Returns a string representation of the Environments

        Arguments:
        environment : integer - The integer matching one of the
                                environments enums.

        Returns a string
        """

        if environment == Environments.OSX:
            return "OS X"
        elif environment == Environments.Windows:
            return "Windows"
        elif environment == Environments.UWP:
            return "Windows Store App"
        elif environment == Environments.Linux:
            return "Linux"
        elif environment == Environments.IOS:
            return "iOS"
        elif environment == Environments.TVOS:
            return "Apple TV OS"
        elif environment == Environments.Android:
            return "Android"
        elif environment == Environments.NoPlatform:
            return "No Platform"
        elif environment == Environments.Apple:
            return "Apple Device"
        else:
            return "Unknown"
