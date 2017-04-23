import inspect
from django.apps import AppConfig as DjangoAppConfig
import django.forms.models


def construct_instance(form, instance, fields=None, exclude=None):
    """
    Taken from django.forms.models.construct_instance
    altered to support cqlengine models (see field_has_default logic)
    """
    from django.db import models
    opts = instance._meta

    cleaned_data = form.cleaned_data
    file_field_list = []
    for field in opts.fields:
        if not field.editable or isinstance(field, models.AutoField) \
                or field.name not in cleaned_data:
            continue
        if fields is not None and field.name not in fields:
            continue
        if exclude and field.name in exclude:
            continue
        # Leave defaults for fields that aren't in POST data, except for
        # checkbox inputs because they don't appear in POST data if not checked

        # cqlengine support logic start
        if inspect.ismethod(field.has_default):
            # django model
            field_has_default = field.has_default()
        else:
            # cqlengine model
            field_has_default = field.has_default
        # cqlengine support logic end

        if (field_has_default and form.add_prefix(field.name) not in
            form.data and not getattr(
                form[field.name].field.widget,
                'dont_use_model_field_default_for_empty_data', False)):
            continue
        # Defer saving file-type fields until after the other fields, so a
        # callable upload_to can use the values from other fields.
        if isinstance(field, models.FileField):
            file_field_list.append(field)
        else:
            field.save_form_data(instance, cleaned_data[field.name])

    for f in file_field_list:
        f.save_form_data(instance, cleaned_data[f.name])

    return instance


# patching so that Django ModelForms can work with cqlengine models
django.forms.models.construct_instance = construct_instance


class AppConfig(DjangoAppConfig):
    name = 'sqladjango'

    def connect(self):
        from sqladjango.utils import get_sqla_connections
        for _, conn in get_sqla_connections():
            conn.connect()

    def import_models(self, *args, **kwargs):
        self.connect()
        return super().import_models(*args, **kwargs)
