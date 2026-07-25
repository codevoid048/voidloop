from django.contrib import admin

from habits.models import Habit, HabitCheckIn


class HabitCheckInInline(admin.TabularInline):
    model = HabitCheckIn
    extra = 0
    fields = ("date", "note", "created_at", "deleted_at")
    readonly_fields = ("created_at", "deleted_at")
    ordering = ("-date",)


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_archived", "sort_order", "created_at")
    list_filter = ("is_archived", "created_at")
    search_fields = ("name", "user__email", "user__username")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
    inlines = [HabitCheckInInline]


@admin.register(HabitCheckIn)
class HabitCheckInAdmin(admin.ModelAdmin):
    list_display = ("habit", "date", "created_at")
    list_filter = ("date",)
    search_fields = ("habit__name", "habit__user__email")
    readonly_fields = ("created_at", "updated_at", "deleted_at")
