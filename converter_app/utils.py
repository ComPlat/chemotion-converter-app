import uuid


def validate_id(profile_id):
    try:
        uuid.UUID(profile_id, version=4)
        return True
    except ValueError:
        return False
