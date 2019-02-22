from django.contrib import admin
from django.shortcuts import redirect, reverse
from .models import Account


# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    """"""
    actions = None
    fields = ['login', 'enabled']

    def add_view(self, request, form_url='', extra_context=None):
        """Redirect user straight to yandex oauth authorization"""
        return redirect(reverse("authorize_account", kwargs={"account_id": 0}))

    def response_change(self, request, obj):
        if not obj.token:
            return redirect(reverse("authorize_account", kwargs={"account_id": obj.id}))
        return super().response_change(request, obj)

admin.site.register(Account, AccountAdmin)