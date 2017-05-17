from django.contrib import admin
from django import forms

from experimenter.experiments.models import Experiment, ExperimentVariant


class BaseVariantInlineAdmin(admin.StackedInline):
    max_num = 1
    model = ExperimentVariant
    prepopulated_fields = {'slug': ('name',)}

    def has_delete_permission(self, request, obj=None):
        return False


class ControlVariantModelForm(forms.ModelForm):

    def save(self, commit=True):
        self.instance.is_control = True
        return super().save(commit=commit)

    class Meta:
        model = ExperimentVariant
        exclude = []


class ControlVariantInlineAdmin(BaseVariantInlineAdmin):
    form = ControlVariantModelForm
    verbose_name = 'Control Variant'
    verbose_name_plural = 'Control Variant'
    fields = ('name', 'slug', 'description', 'value')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=True)


class ExperimentVariantInlineAdmin(BaseVariantInlineAdmin):
    verbose_name = 'Experiment Variant'
    verbose_name_plural = 'Experiment Variant'
    fields = ('name', 'slug', 'threshold', 'description', 'value')

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_control=False)


class ExperimentAdmin(admin.ModelAdmin):
    inlines = (ControlVariantInlineAdmin, ExperimentVariantInlineAdmin,)
    prepopulated_fields = {'slug': ('name',)}
    fields = (
        'status',
        'created_date',
        'start_date',
        'end_date',
        'project',
        'name',
        'slug',
        'objectives',
        'success_criteria',
        'analysis',
    )
    list_display = (
        'name', 'project', 'status', 'created_date', 'start_date', 'end_date')

    readonly_fields = ('created_date', 'start_date', 'end_date')

    def get_readonly_fields(self, request, obj=None):
        db_complete = False
        if obj is not None:
            db_obj = Experiment.objects.get(pk=obj.pk)
            db_complete = db_obj.is_complete

        if obj is None or db_complete:
            return super().get_readonly_fields(request, obj=obj) + ('status',)

        return super().get_readonly_fields(request, obj=obj)


admin.site.register(Experiment, ExperimentAdmin)
