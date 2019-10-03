from types import SimpleNamespace
from juju.framework import Object, Event, EventBase, EventsBase


class InstallEvent(EventBase):
    pass

class StartEvent(EventBase):
    pass

class StopEvent(EventBase):
    pass

class ConfigChangedEvent(EventBase):
    pass

class UpdateStatusEvent(EventBase):
    pass

class UpgradeCharmEvent(EventBase):
    pass

class PreSeriesUpgradeEvent(EventBase):
    pass

class PostSeriesUpgradeEvent(EventBase):
    pass

class LeaderElectedEvent(EventBase):
    pass

class LeaderSettingsChangedEvent(EventBase):
    pass


class RelationEventBase(EventBase):
    pass


class RelationJoinedEvent(RelationEventBase):
    pass

class RelationChangedEvent(RelationEventBase):
    pass

class RelationDepartedEvent(RelationEventBase):
    pass

class RelationBrokenEvent(RelationEventBase):
    pass


class StorageEventBase(EventBase):
    pass


class StorageAttachedEvent(StorageEventBase):
    pass

class StorageDetachingEvent(StorageEventBase):
    pass


class CharmEvents(EventsBase):

    install = Event(InstallEvent)
    start = Event(StartEvent)
    stop = Event(StopEvent)
    update_status = Event(UpdateStatusEvent)
    config_changed = Event(ConfigChangedEvent)
    upgrade_charm = Event(UpgradeCharmEvent)
    pre_series_upgrade = Event(PreSeriesUpgradeEvent)
    post_series_upgrade = Event(PostSeriesUpgradeEvent)
    leader_elected = Event(LeaderElectedEvent)
    leader_settings_changed = Event(LeaderSettingsChangedEvent)

    @property
    def relation(self):
        """Convenience accessor for accessing relation events by relation name.

        Example usage::

            framework.observe(charm.on.relation["db"].joined, charm)
            charm.on.relation["db"].broken.emit()
        """
        groups = {}
        for event_kind, bound_event in self.events().items():
            if '_relation_' in event_kind:
                relation_name, _, event_name = event_kind.split('_')
                ns = groups.setdefault(relation_name, SimpleNamespace())
                setattr(ns, event_name, bound_event)
        return groups

    @property
    def storage(self):
        """Convenience accessor for accessing storage events by storage name.

        Example usage::

            framework.observe(charm.on.storage["cache"].attached, charm)
            charm.on.storage["cache"].detaching.emit()
        """
        groups = {}
        for event_kind, bound_event in self.events().items():
            if '_storage_' in event_kind:
                storage_name, _, event_name = event_kind.split('_')
                ns = groups.setdefault(storage_name, SimpleNamespace())
                setattr(ns, event_name, bound_event)
        return groups


class CharmBase(Object):

    on = CharmEvents()

    def __init__(self, framework, key, metadata):
        super().__init__(framework, key)
        self.metadata = metadata

        for relation_name in self.metadata.relations:
            self.on.define_event(f'{relation_name}_relation_joined', RelationJoinedEvent)
            self.on.define_event(f'{relation_name}_relation_changed', RelationChangedEvent)
            self.on.define_event(f'{relation_name}_relation_departed', RelationDepartedEvent)
            self.on.define_event(f'{relation_name}_relation_broken', RelationBrokenEvent)

        for storage_name in metadata.storage:
            self.on.define_event(f'{storage_name}_storage_attached', StorageAttachedEvent)
            self.on.define_event(f'{storage_name}_storage_detaching', StorageDetachingEvent)


class CharmMetadata:
    """Object containing the metadata for the charm.

    Supported fields are:

        * ``name``
        * ``summary``
        * ``description``
        * ``maintainers``
        * ``tags``
        * ``terms``
        * ``series``
        * ``subordinate``
        * ``min_juju_version``
        * ``requires``
        * ``provides``
        * ``peers``
        * ``relations``
        * ``storage``
        * ``resources``
        * ``payloads``
        * ``extra_bindings``

    The ``maintainers``, ``tags``, ``terms``, ``series``, and ``extra_bindings``
    attributes are all tuples of strings.  The ``requires``, ``provides``,
    `peers``, ``relations``, ``storage``, ``resources``, and ``payloads``
    attributes are all mappings of names to instances of the respective
    :class:`RelationDefinition`, :class:`StorageDefinition`, :class:`ResourceDefinition`,
    or :class:`PayloadDefinition`.

    The ``relations`` attribute is a convenience accessor which includes all of
    the ``requires``, ``provides``, and ``peers`` :class:`RelationDefinition`_
    items.  If needed, the role of the relation definition can be obtained from
    its ``role`` attribute.
    """
    def __init__(self, raw=None):
        raw = raw or {}
        self.name = raw.get('name', '')
        self.summary = raw.get('summary', '')
        self.description = raw.get('description', '')
        maintainers = []
        if 'maintainer' in raw:
            maintainers.append(raw['maintainer'])
        if 'maintainers' in raw:
            maintainers.extend(raw['maintainers'])
        self.maintainers = tuple(maintainers)
        self.tags = tuple(raw.get('tags', []))
        self.terms = tuple(raw.get('terms', []))
        self.series = tuple(raw.get('series', []))
        self.subordinate = raw.get('subordinate', False)
        self.min_juju_version = raw.get('min-juju-version')
        self.requires = {name: RelationDefinition('requires', name, rel)
                         for name, rel in raw.get('requires', {}).items()}
        self.provides = {name: RelationDefinition('provides', name, rel)
                         for name, rel in raw.get('provides', {}).items()}
        self.peers = {name: RelationDefinition('peers', name, rel)
                      for name, rel in raw.get('peers', {}).items()}
        self.relations = {}
        self.relations.update(self.requires)
        self.relations.update(self.provides)
        self.relations.update(self.peers)
        self.storage = {name: StorageDefinition(name, store)
                        for name, store in raw.get('storage', {}).items()}
        self.resources = {name: ResourceDefinition(name, res)
                          for name, res in raw.get('resources', {}).items()}
        self.payloads = {name: PayloadDefinition(name, payload)
                         for name, payload in raw.get('payloads', {}).items()}
        self.extra_bindings = tuple(raw.get('extra-bindings', {}))


class RelationDefinition:
    """Object containing metadata about a relation definition.

    Supported fields are:

        * ``role``
        * ``relation_name``
        * ``interface_name``
        * ``scope``
    """
    def __init__(self, role, relation_name, raw):
        self.role = role
        self.relation_name = relation_name
        self.interface_name = raw['interface']
        self.scope = raw.get('scope')


class StorageDefinition:
    """Object containing metadata about a storage definition.

    Supported fields are:
    """
    def __init__(self, name, raw):
        self.storage_name = name
        self.type = raw['type']
        self.description = raw.get('description', '')
        self.shared = raw.get('shared', False)
        self.read_only = raw.get('read-only', False)
        self.minimum_size = raw.get('minimum-size')
        self.location = raw.get('location')
        self.is_multiple = 'multiple' in raw
        self.range = None
        if self.is_multiple:
            range = raw['multiple']['range']
            if '-' not in range:
                self.range = (int(range), int(range))
            else:
                range = range.split('-')
                self.range = (int(range[0]), int(range[1]) if range[1] else None)


class ResourceDefinition:
    """Object containing metadata about a resource definition.

    Supported fields are:
    """
    def __init__(self, name, raw):
        self.resource_name = name
        self.type = raw['type']
        self.filename = raw['filename']
        self.description = raw.get('description', '')


class PayloadDefinition:
    """Object containing metadata about a payload definition.

    Supported fields are:
    """
    def __init__(self, name, raw):
        self.payload_name = name
        self.type = raw['type']
