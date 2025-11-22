from django.contrib import admin
from account.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserModelAdmin(BaseUserAdmin):
  list_display = (
      'id', 'email', 'name', 'first_name', 'last_name', 'phone_number',
      'is_email_verified', 'is_active', 'is_admin', 'created_at'
  )
  list_filter = ('is_admin', 'is_active', 'is_email_verified', 'created_at')
  fieldsets = (
      ('Credentials', {'fields': ('email', 'password')}),
      ('Personal info', {'fields': ('name', 'first_name', 'last_name', 'phone_number', 'avatar', 'tc')}),
      ('Status', {'fields': ('is_active', 'is_email_verified')}),
      ('Permissions', {'fields': ('is_admin',)}),
      ('Timestamps', {'fields': ('created_at', 'updated_at')}),
  )
  add_fieldsets = (
      (None, {
          'classes': ('wide',),
          'fields': ('email', 'name', 'tc', 'password1', 'password2'),
      }),
  )
  readonly_fields = ('created_at', 'updated_at')
  search_fields = ('email', 'name', 'first_name', 'last_name', 'phone_number')
  ordering = ('email', 'id')
  actions = ['mark_email_verified', 'mark_email_unverified', 'activate_users', 'deactivate_users']
  actions.append('safe_delete_users')
  filter_horizontal = ()

  def mark_email_verified(self, request, queryset):
      from django.db import IntegrityError
      try:
          queryset.update(is_email_verified=True)
      except IntegrityError:
          for obj in queryset:
              obj.is_email_verified = True
              obj.save()
  mark_email_verified.short_description = 'Mark selected users as email verified'

  def mark_email_unverified(self, request, queryset):
      from django.db import IntegrityError
      try:
          queryset.update(is_email_verified=False)
      except IntegrityError:
          for obj in queryset:
              obj.is_email_verified = False
              obj.save()
  mark_email_unverified.short_description = 'Mark selected users as email unverified'

  def activate_users(self, request, queryset):
      from django.db import IntegrityError
      try:
          queryset.update(is_active=True)
      except IntegrityError:
          for obj in queryset:
              obj.is_active = True
              obj.save()
  activate_users.short_description = 'Activate selected users'

  def deactivate_users(self, request, queryset):
      from django.db import IntegrityError
      try:
          queryset.update(is_active=False)
      except IntegrityError:
          for obj in queryset:
              obj.is_active = False
              obj.save()
  
  def get_actions(self, request):
      actions = super().get_actions(request)
      if 'delete_selected' in actions:
          del actions['delete_selected']
      return actions

  def save_model(self, request, obj, form, change):
      from django.db import IntegrityError, transaction
      try:
          with transaction.atomic():
              super().save_model(request, obj, form, change)
      except IntegrityError:
          try:
              obj.save()
          except Exception:
              from django.contrib import messages
              messages.error(request, 'Could not save due to a database constraint.')

  def log_addition(self, request, object, message):
      return None

  def log_change(self, request, object, message):
      return None

  def log_deletion(self, request, object, object_repr):
      return None

  def safe_delete_users(self, request, queryset):
      from django.db import IntegrityError
      from django.db.models.deletion import ProtectedError
      from django.contrib.admin.models import LogEntry
      deleted = 0
      deactivated = 0
      for obj in queryset:
          try:
              has_logs = LogEntry.objects.filter(user_id=obj.pk).exists()
          except Exception:
              has_logs = True
          if has_logs:
              try:
                  obj.is_active = False
                  obj.save()
                  deactivated += 1
              except Exception:
                  pass
              continue
          try:
              obj.delete()
              deleted += 1
          except (ProtectedError, IntegrityError):
              try:
                  obj.is_active = False
                  obj.save()
                  deactivated += 1
              except Exception:
                  pass
      self.message_user(request, f"Deleted: {deleted}, Deactivated: {deactivated}")
  safe_delete_users.short_description = 'Safely delete selected users (deactivate when referenced)'
  deactivate_users.short_description = 'Deactivate selected users'

admin.site.register(User, UserModelAdmin)