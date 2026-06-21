import os
from config.settings import Settings
from core.serializer import EventSerializer

class LocalChangeHandler:
    def __init__(self, mesh_engine):
        self.mesh_engine = mesh_engine

    def on_local_file_changed(self, event):
        app_settings = Settings()
        action = event.event_type.upper()
        
        src_name = os.path.relpath(event.src_path, app_settings.sync_path)
        dest_name = None
        
        if hasattr(event, 'dest_path') and event.dest_path:
            dest_name = os.path.relpath(event.dest_path, app_settings.sync_path)
            
        payload = EventSerializer.serialize(
            action=action,
            src_name=src_name,
            dest_name=dest_name,
            sync_path=app_settings.sync_path
        )
        
        if self.mesh_engine:
            self.mesh_engine.broadcast_payload(payload)