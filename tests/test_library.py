"""Test the various features of our custom library object.
"""

from nose.tools import assert_raises

from coffin.common import get_env
from jinja2 import TemplateAssertionError as Jinja2TemplateAssertionError
from django.template import Template, Context, \
    TemplateSyntaxError as DjangoTemplateSyntaxError


def test_nodes_and_extensions():
    """Test availability of registered nodes/extensions.
    """
    env = get_env()

    # Jinja2 extensions, loaded from a Coffin library
    assert env.from_string('a{% foo %}b').render() == 'a{foo}b'

    # Django tags, loaded from a Coffin library
    assert Template('{% load foo_tag %}a{% foo_coffin %}b').render({}) == 'a{foo}b'


def test_filters():
    """Test availability of registered filters.
    """
    env = get_env()

    # Filter registered with a Coffin library is available in Django and Jinja2
    assert env.from_string('a{{ "b"|foo }}c').render() == 'a{foo}c'
    assert Template('{% load foo_filter %}a{{ "b"|foo }}c').render(Context()) == 'a{foo}c'

    # Filter registered with a Django library is not available in Jinja2
    Template('{% load foo_filter_django %}{{ "b"|foo_django }}').render(Context())
    assert_raises(Jinja2TemplateAssertionError,
                  env.from_string, 'a{{ "b"|foo_django }}c')

    # Some filters, while registered with a Coffin library, are only
    # available in Jinja2:
    # - when using @environmentfilter
    env.from_string('{{ "b"|environment }}')
    assert_raises(Exception, Template, '{% load jinjafilters %}{{ "b"|environment }}')
    # - when using @contextfilter
    env.from_string('{{ "b"|context }}')
    assert_raises(Exception, Template, '{% load jinjafilters %}{{ "b"|context }}')
    # - when requiring more than one argument
    env.from_string('{{ "b"|multiarg(1,2) }}')
    assert_raises(Exception, Template, '{% load jinjafilters %}{{ "b"|multiarg }}')


def test_filter_compat_safestrings():
    """Test filter compatibility layer with respect to safe strings.
    """
    env = get_env()
    env.autoescape = True


    # Jinja-style safe output strings are considered "safe" by both engines
    assert env.from_string('{{ "<b>"|jinja_safe_output }}').render() == '<b>'
    # TODO: The below actually works regardless of our converting between
    # the same string types: Jinja's Markup() strings are actually immune
    # to Django's escape() attempt, since they have a custom version of
    # replace() that operates on an already escaped version.
    assert Template('{% load compat_filters %}{{ "<b>"|jinja_safe_output }}').render(Context()) == '<b>'

    # Unsafe, unmarked output strings are considered "unsafe" by both engines
    assert env.from_string('{{ "<b>"|unsafe_output }}').render() == '&lt;b&gt;'
    assert Template('{% load compat_filters %}{{ "<b>"|unsafe_output }}').render(Context()) == '&lt;b&gt;'

    # Django-style safe output strings are considered "safe" by both engines
    assert env.from_string('{{ "<b>"|django_safe_output }}').render() == '<b>'
    assert Template('{% load compat_filters %}{{ "<b>"|django_safe_output }}').render(Context()) == '<b>'


def test_filter_compat_escapetrings():
    """Test filter compatibility layer with respect to strings flagged as
    "wanted for escaping".
    """
    env = get_env()
    env.autoescape = False

    # Django-style "force escaping" works in both engines
    assert env.from_string('{{ "<b>"|django_escape_output }}').render() == '&lt;b&gt;'
    assert Template('{% load compat_filters %}{{ "<b>"|django_escape_output }}').render(Context()) == '&lt;b&gt;'


def test_filter_compat_other():
    """Test other features of the filter compatibility layer.
    """
    env = get_env()

    # A Django filter with @needs_autoescape works in Jinja2
    env.autoescape = True
    assert env.from_string('{{ "b"|needing_autoescape }}').render() == 'True'
    env.autoescape = False
    assert env.from_string('{{ "b"|needing_autoescape }}').render() == 'False'

    # TODO: test @stringfilter