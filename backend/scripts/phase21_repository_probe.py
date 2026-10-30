from app.modules.channels.repository import WorkspaceChannelRepository

print("MODULE:", WorkspaceChannelRepository.__module__)
print("FILE:", WorkspaceChannelRepository.__module__)
print("GET_MESSAGE:", hasattr(WorkspaceChannelRepository, "get_message"))
print("UPDATE_MESSAGE:", hasattr(WorkspaceChannelRepository, "update_message"))
print("DELETE_MESSAGE:", hasattr(WorkspaceChannelRepository, "delete_message"))

print("METHODS:")
for name in dir(WorkspaceChannelRepository):
    if "message" in name.lower():
        print(name)
