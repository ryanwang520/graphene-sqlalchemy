from graphene import Enum, List, ObjectType, Schema, String
import sqlalchemy as sa

from ..utils import get_session, sort_enum_for_model, sort_argument_for_model
from .models import Pet, Editor


def test_get_session():
    session = 'My SQLAlchemy session'

    class Query(ObjectType):
        x = String()

        def resolve_x(self, info):
            return get_session(info.context)

    query = '''
        query ReporterQuery {
            x
        }
    '''

    schema = Schema(query=Query)
    result = schema.execute(query, context_value={'session': session})
    assert not result.errors
    assert result.data['x'] == session


def test_sort_enum_for_model():
    enum = sort_enum_for_model(Pet)
    assert isinstance(enum, type(Enum))
    assert str(enum) == 'PetSortEnum'
    for col in sa.inspect(Pet).columns:
        assert hasattr(enum, col.name + '_asc')
        assert hasattr(enum, col.name + '_desc')


def test_sort_enum_for_model_custom_naming():
    enum = sort_enum_for_model(Pet, 'Foo',
                               lambda n, d: n.upper() + ('A' if d else 'D'))
    assert str(enum) == 'Foo'
    for col in sa.inspect(Pet).columns:
        assert hasattr(enum, col.name.upper() + 'A')
        assert hasattr(enum, col.name.upper() + 'D')


def test_enum_cache():
    assert sort_enum_for_model(Editor) is sort_enum_for_model(Editor)


def test_sort_argument_for_model():
    arg = sort_argument_for_model(Pet)

    assert isinstance(arg.type, List)
    assert arg.default_value == [Pet.id.name + '_asc']
    assert arg.type.of_type == sort_enum_for_model(Pet)


def test_sort_argument_for_model_no_default():
    arg = sort_argument_for_model(Pet, False)

    assert arg.default_value is None


def test_sort_argument_for_model_multiple_pk():
    Base = sa.ext.declarative.declarative_base()

    class MultiplePK(Base):
        foo = sa.Column(sa.Integer, primary_key=True)
        bar = sa.Column(sa.Integer, primary_key=True)
        __tablename__ = 'MultiplePK'

    arg = sort_argument_for_model(MultiplePK)
    assert set(arg.default_value) == set((MultiplePK.foo.name + '_asc',
                                          MultiplePK.bar.name + '_asc'))
