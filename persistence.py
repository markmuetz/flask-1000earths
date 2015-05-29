import os
import datetime as dt
from glob import glob
import ConfigParser

DATE_FMT = '%Y-%m-%d %H:%M:%S'

class Objects(object):
    obj_cls = None
    _objects = None

    def list(self):
        filenames = glob('site/*.cfg')
        filenames.extend(glob('site/*/*.cfg'))
        obj_paths = []
        for fn in filenames:
            cp = ConfigParser.ConfigParser()
            cp.read(fn)
            if cp.has_section(self.obj_cls.__name__):
                obj_paths.append(os.path.relpath(os.path.splitext(fn)[0], 'site'))
        return obj_paths

    def _load_all(self, content=True):
        obj_paths = self.list()
        self._objects = []
        for path in obj_paths:
            self._objects.append(self.get(path, content))


    def all(self):
        if not self._objects:
            self._load_all()
        return self._objects


    def filter(self, **kwargs):
        if not self._objects:
            self._load_all()
        objs = []
        for obj in self._objects:
            ret_obj = obj
            for k, v in kwargs.items():
                if not getattr(obj, k) == v:
                    ret_obj = None
                    break
            if ret_obj:
                objs.append(ret_obj)
        return objs


    def get(self, path, content=True):
        cfg_filename = 'site/{0}.cfg'.format(path)
        html_filename = 'site/{0}.html'.format(path)
        md_filename = 'site/{0}.md'.format(path)
        obj_dct = {}
        obj_dct['path'] = path

        cp = ConfigParser.ConfigParser()
        cp.read(cfg_filename)

        page_type = self.obj_cls.__name__
        fields = self.obj_cls.fields.items()
        for field_name, field in fields:
            if field.ftype == dt.datetime:
                date_str = cp.get(page_type, field_name)
                obj_dct[field_name] = dt.datetime.strptime(date_str, DATE_FMT)
            elif field.ftype == bool:
                val = cp.get(page_type, field_name)
                if val.lower() == 'true':
                    val = True
                elif val.lower() == 'false':
                    val = True
                else:
                    raise Exception('{0} not recognised as bool'.format(val))
                obj_dct[field_name] = val
            elif field.ftype in [int, float]:
                val = cp.get(page_type, field_name)
                val = field.ftype(val)
                obj_dct[field_name] = val
            else:
                obj_dct[field_name] = cp.get(page_type, field_name)

        if content:
            content_fields = self.obj_cls.content_fields.items()
            for content_field_name, content_field in content_fields:
                content_filename = 'site/{0}.{1}'.format(path, content_field.ctype)
                with open(content_filename, 'r') as f:
                    obj_dct[content_field_name] = f.read()

        obj = self.obj_cls(**obj_dct)
        return obj

    def save(self, obj):
        cfg_filename = 'site/{0}.cfg'.format(obj.path)

        cp = ConfigParser.ConfigParser()
        # cp.read(cfg_filename)

        page_type = type(obj).__name__
        cp.add_section(page_type)
        fields = type(obj).fields.items()
        for field_name, field in fields:
            if field.ftype == dt.datetime:
                date_str = getattr(obj, field_name)
                cp.set(page_type, field_name, dt.datetime.strftime(date_str, DATE_FMT))
            else:
                cp.set(page_type, field_name, getattr(obj, field_name))

        with open(cfg_filename, 'w') as f:
            cp.write(f)

        content_fields = type(obj).content_fields.items()
        for content_field_name, content_field in content_fields:
            content_filename = 'site/{0}.{1}'.format(obj.path, content_field.ctype)
            with open(content_filename, 'w') as f:
                f.write(getattr(obj, content_field_name))

        # if page_type == 'post':
            # posts()
        # elif page_type == 'page':
            # site()

    def delete(self, obj):
        path = obj.path
        cfg_filename = 'site/{0}.cfg'.format(path)
        md_filename = 'site/{0}.md'.format(path)
        html_filename = 'site/{0}.html'.format(path)
        for filename in [cfg_filename, md_filename, html_filename]:
            os.remove(filename)


class Field(object):
    def __init__(self, ftype, required=True):
        self.ftype = ftype
        self.required = required

class ContentField(object):
    def __init__(self, ctype, required=True):
        if ctype not in ['md', 'html']:
            raise Exception('Unkown content type: {0}'.format(ctype))
        self.ctype = ctype
        self.required = required

class MetaModel(type):
    def __new__(cls, clsname, bases, dct):
        # print('Creating class: {0}'.format(clsname))
        # print(dct)
        dct['objects'] = Objects()
        dct['fields'] = {}
        dct['content_fields'] = {}
        for k, v in dct.items():
            if isinstance(v, Field):
                dct['fields'][k] = v
            if isinstance(v, ContentField):
                dct['content_fields'][k] = v

        obj_cls = super(MetaModel, cls).__new__(cls, clsname, bases, dct)
        dct['objects'].obj_cls = obj_cls
        return obj_cls


class Model(object):
    __metaclass__ = MetaModel

    def __init__(self, **kwargs):
        # print(kwargs)
        if 'path' not in kwargs:
            raise Exception('path missing')
        self.path = kwargs.pop('path')

        for field_name, field in type(self).fields.items():
            # Default?
            if field.required and not field_name in kwargs:
                raise Exception('Missing kwargs: {0}'.format(field_name))
            val = kwargs.pop(field_name)
            if type(val) != field.ftype:
                raise Exception('Wrong type for {0} (should be {1}'.format(field_name, field.ftype))
            setattr(self, field_name, val)

        for field_name, field in type(self).content_fields.items():
            # Default?
            if field.required and not field_name in kwargs:
                raise Exception('Missing kwargs: {0}'.format(field_name))
            val = kwargs.pop(field_name)
            if type(val) != str:
                raise Exception('Wrong type for {0} (should be <type: str>'.format(field_name, val))
            setattr(self, field_name, val)

        if len(kwargs) != 0:
            raise Exception('Leftover kwargs: {0}'.format(kwargs))

    def save(self):
        type(self).objects.save(self)

    def delete(self):
        type(self).objects.delete(self)
