from juju.framework import Object, Event, EventBase, EventsBase


class InstallEvent(EventBase): pass
class StartEvent(EventBase): pass
class StopEvent(EventBase): pass
class ConfigChangedEvent(EventBase): pass
class UpdateStatusEvent(EventBase): pass
class UpgradeCharmEvent(EventBase): pass
class PreSeriesUpgradeEvent(EventBase): pass
class PostSeriesUpgradeEvent(EventBase): pass
class LeaderElectedEvent(EventBase): pass
class LeaderSettingsChangedEvent(EventBase): pass

# TODO: These relations will need to be given more contextual info about the event
class RelationJoinedEvent(EventBase): pass
class RelationChangedEvent(EventBase): pass
class RelationDepartedEvent(EventBase): pass
class RelationBrokenEvent(EventBase): pass
class StorageAttachedEvent(EventBase): pass
class StorageDetachingEvent(EventBase): pass


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


class CharmBase(Object):

    on = CharmEvents()

    def __init__(self, framework, key, metadata):
        super().__init__(framework, key)
        self.metadata = metadata

        for role in ('requires', 'provides', 'peers'):
            for relation_name in metadata.get(role, ()):
                self.on.define_event(f'{relation_name}_relation_joined',
                                     RelationJoinedEvent)
                self.on.define_event(f'{relation_name}_relation_changed',
                                     RelationChangedEvent)
                self.on.define_event(f'{relation_name}_relation_departed',
                                     RelationDepartedEvent)
                self.on.define_event(f'{relation_name}_relation_broken',
                                     RelationBrokenEvent)

        for storage_name in metadata.get('storage', ()):
            self.on.define_event(f'{storage_name}_storage_attached',
                                 StorageAttachedEvent)
            self.on.define_event(f'{storage_name}_storage_detaching',
                                 StorageDetachingEvent)
