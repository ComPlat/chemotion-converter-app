from jsonschema.validators import validator_for
from referencing import Registry, Resource


class SchemaRegistry:
    """
    This calls manages all reader. It must be used as Singleton
    """
    _instance = None
    _schema_store = []
    _registry = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        """
        Singleton constructor
        :return: Readers Singleton
        """
        if cls._instance is None:
            cls._instance = cls.__new__(cls)

        return cls._instance

    @property
    def registry(self):
        return self._schema_store

    def validator_for(self, id: str):
        if self._registry is None:
            self._registry = Registry().with_resources(self._schema_store)
        schema = self._registry.get(id).contents
        return validator_for(schema)(schema, registry=self._registry)


    def register(self, schema: dict):
        """
        Register a shcema
        :param reader:
        :param json_schema: schema.org schema
        :return:
        """
        self._schema_store.append((schema["$id"], Resource.from_contents(schema)))
