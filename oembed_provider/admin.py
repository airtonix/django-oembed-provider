from django.contrib import admin
from oembed.models import StoredProvider, StoredOEmbed


class StoredProviderAdmin(admin.ModelAdmin):
    list_display = ('wildcard_regex', 'endpoint_url', 'active', 'provides')
    list_filter = ('active', 'provides')
    search_fields = ('regex',)

    actions = ['activate', 'deactivate']

    def activate(self, request, queryset):
        for item in queryset:
            item.active = True
            item.save()
    activate.short_description = "Activate selected Stored Providers"

    def deactivate(self, request, queryset):
        for item in queryset:
            item.active = False
            item.save()
    deactivate.short_description = "Deactivate selected Stored Providers"


class StoredOEmbedAdmin(admin.ModelAdmin):
    list_display = ('match', 'date_added')
    search_fields = ('match',)


admin.site.register(StoredProvider, StoredProviderAdmin)
admin.site.register(StoredOEmbed, StoredOEmbedAdmin)
