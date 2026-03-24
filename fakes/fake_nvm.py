"""Fake NVM for testing without hardware."""


def create_fake_nvm(size: int = 512) -> bytearray:
    """Create a fake NVM backed by a bytearray.

    :param size: Size of the NVM in bytes
    :return: A bytearray that behaves like microcontroller.nvm
    """
    return bytearray(size)
