from thundra.plugins import PluginSource, Plugin
# print(list(Plugin.find_by_author('krypton-byte')))


t = PluginSource("krypton-byte", "test-plugin")
t.download_head("master").install()
