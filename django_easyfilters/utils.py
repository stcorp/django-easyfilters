from django.db.models.constants import LOOKUP_SEP
from django.db.models.base import ForeignObjectRel


def get_model_field(model, f):
    parts = f.split(LOOKUP_SEP)
    opts = model._meta
    for name in parts[:-1]:
        rel = opts.get_field(name)
        if isinstance(rel, ForeignObjectRel):
            model = rel.related_model
            opts = model._meta
        else:
            model = rel.remote_field.model
            opts = model._meta
    rel = opts.get_field(parts[-1])
    return rel, rel.many_to_many
