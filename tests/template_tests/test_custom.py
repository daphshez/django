from __future__ import unicode_literals

import os

from django.template import Context, Engine, Template, TemplateSyntaxError
from django.template.base import Node
from django.test import SimpleTestCase, ignore_warnings
from django.test.utils import extend_sys_path
from django.utils.deprecation import RemovedInDjango20Warning

from .templatetags import custom, inclusion
from .utils import ROOT


class CustomFilterTests(SimpleTestCase):

    def test_filter(self):
        t = Template("{% load custom %}{{ string|trim:5 }}")
        self.assertEqual(
            t.render(Context({"string": "abcdefghijklmnopqrstuvwxyz"})),
            "abcde"
        )


class TagTestCase(SimpleTestCase):

    def verify_tag(self, tag, name):
        self.assertEqual(tag.__name__, name)
        self.assertEqual(tag.__doc__, 'Expected %s __doc__' % name)
        self.assertEqual(tag.__dict__['anything'], 'Expected %s __dict__' % name)


class SimpleTagTests(TagTestCase):

    def test_simple_tags(self):
        c = Context({'value': 42})

        templates = [
            ('{% load custom %}{% no_params %}', 'no_params - Expected result'),
            ('{% load custom %}{% one_param 37 %}', 'one_param - Expected result: 37'),
            ('{% load custom %}{% explicit_no_context 37 %}', 'explicit_no_context - Expected result: 37'),
            ('{% load custom %}{% no_params_with_context %}',
                'no_params_with_context - Expected result (context value: 42)'),
            ('{% load custom %}{% params_and_context 37 %}',
                'params_and_context - Expected result (context value: 42): 37'),
            ('{% load custom %}{% simple_two_params 37 42 %}', 'simple_two_params - Expected result: 37, 42'),
            ('{% load custom %}{% simple_one_default 37 %}', 'simple_one_default - Expected result: 37, hi'),
            ('{% load custom %}{% simple_one_default 37 two="hello" %}',
                'simple_one_default - Expected result: 37, hello'),
            ('{% load custom %}{% simple_one_default one=99 two="hello" %}',
                'simple_one_default - Expected result: 99, hello'),
            ('{% load custom %}{% simple_one_default 37 42 %}',
                'simple_one_default - Expected result: 37, 42'),
            ('{% load custom %}{% simple_unlimited_args 37 %}', 'simple_unlimited_args - Expected result: 37, hi'),
            ('{% load custom %}{% simple_unlimited_args 37 42 56 89 %}',
                'simple_unlimited_args - Expected result: 37, 42, 56, 89'),
            ('{% load custom %}{% simple_only_unlimited_args %}', 'simple_only_unlimited_args - Expected result: '),
            ('{% load custom %}{% simple_only_unlimited_args 37 42 56 89 %}',
                'simple_only_unlimited_args - Expected result: 37, 42, 56, 89'),
            ('{% load custom %}{% simple_unlimited_args_kwargs 37 40|add:2 56 eggs="scrambled" four=1|add:3 %}',
                'simple_unlimited_args_kwargs - Expected result: 37, 42, 56 / eggs=scrambled, four=4'),
        ]

        for entry in templates:
            t = Template(entry[0])
            self.assertEqual(t.render(c), entry[1])

        for entry in templates:
            t = Template("%s as var %%}Result: {{ var }}" % entry[0][0:-2])
            self.assertEqual(t.render(c), "Result: %s" % entry[1])

    def test_simple_tag_errors(self):
        errors = [
            ("'simple_one_default' received unexpected keyword argument 'three'",
                '{% load custom %}{% simple_one_default 99 two="hello" three="foo" %}'),
            ("'simple_two_params' received too many positional arguments",
                '{% load custom %}{% simple_two_params 37 42 56 %}'),
            ("'simple_one_default' received too many positional arguments",
                '{% load custom %}{% simple_one_default 37 42 56 %}'),
            ("'simple_unlimited_args_kwargs' received some positional argument(s) after some keyword argument(s)",
                '{% load custom %}{% simple_unlimited_args_kwargs 37 40|add:2 eggs="scrambled" 56 four=1|add:3 %}'),
            ("'simple_unlimited_args_kwargs' received multiple values for keyword argument 'eggs'",
                '{% load custom %}{% simple_unlimited_args_kwargs 37 eggs="scrambled" eggs="scrambled" %}'),
        ]

        for entry in errors:
            with self.assertRaisesMessage(TemplateSyntaxError, entry[0]):
                Template(entry[1])

        for entry in errors:
            with self.assertRaisesMessage(TemplateSyntaxError, entry[0]):
                Template("%s as var %%}" % entry[1][0:-2])

    def test_simple_tag_registration(self):
        # Test that the decorators preserve the decorated function's docstring, name and attributes.
        self.verify_tag(custom.no_params, 'no_params')
        self.verify_tag(custom.one_param, 'one_param')
        self.verify_tag(custom.explicit_no_context, 'explicit_no_context')
        self.verify_tag(custom.no_params_with_context, 'no_params_with_context')
        self.verify_tag(custom.params_and_context, 'params_and_context')
        self.verify_tag(custom.simple_unlimited_args_kwargs, 'simple_unlimited_args_kwargs')
        self.verify_tag(custom.simple_tag_without_context_parameter, 'simple_tag_without_context_parameter')

    def test_simple_tag_missing_context(self):
        # The 'context' parameter must be present when takes_context is True
        msg = (
            "'simple_tag_without_context_parameter' is decorated with "
            "takes_context=True so it must have a first argument of 'context'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template('{% load custom %}{% simple_tag_without_context_parameter 123 %}')


class InclusionTagTests(TagTestCase):

    def test_inclusion_tags(self):
        c = Context({'value': 42})

        templates = [
            ('{% load inclusion %}{% inclusion_no_params %}', 'inclusion_no_params - Expected result\n'),
            ('{% load inclusion %}{% inclusion_one_param 37 %}', 'inclusion_one_param - Expected result: 37\n'),
            ('{% load inclusion %}{% inclusion_explicit_no_context 37 %}',
                'inclusion_explicit_no_context - Expected result: 37\n'),
            ('{% load inclusion %}{% inclusion_no_params_with_context %}',
                'inclusion_no_params_with_context - Expected result (context value: 42)\n'),
            ('{% load inclusion %}{% inclusion_params_and_context 37 %}',
                'inclusion_params_and_context - Expected result (context value: 42): 37\n'),
            ('{% load inclusion %}{% inclusion_two_params 37 42 %}',
                'inclusion_two_params - Expected result: 37, 42\n'),
            ('{% load inclusion %}{% inclusion_one_default 37 %}', 'inclusion_one_default - Expected result: 37, hi\n'),
            ('{% load inclusion %}{% inclusion_one_default 37 two="hello" %}',
                'inclusion_one_default - Expected result: 37, hello\n'),
            ('{% load inclusion %}{% inclusion_one_default one=99 two="hello" %}',
                'inclusion_one_default - Expected result: 99, hello\n'),
            ('{% load inclusion %}{% inclusion_one_default 37 42 %}',
                'inclusion_one_default - Expected result: 37, 42\n'),
            ('{% load inclusion %}{% inclusion_unlimited_args 37 %}',
                'inclusion_unlimited_args - Expected result: 37, hi\n'),
            ('{% load inclusion %}{% inclusion_unlimited_args 37 42 56 89 %}',
                'inclusion_unlimited_args - Expected result: 37, 42, 56, 89\n'),
            ('{% load inclusion %}{% inclusion_only_unlimited_args %}',
                'inclusion_only_unlimited_args - Expected result: \n'),
            ('{% load inclusion %}{% inclusion_only_unlimited_args 37 42 56 89 %}',
                'inclusion_only_unlimited_args - Expected result: 37, 42, 56, 89\n'),
            ('{% load inclusion %}{% inclusion_unlimited_args_kwargs 37 40|add:2 56 eggs="scrambled" four=1|add:3 %}',
                'inclusion_unlimited_args_kwargs - Expected result: 37, 42, 56 / eggs=scrambled, four=4\n'),
        ]

        for entry in templates:
            t = Template(entry[0])
            self.assertEqual(t.render(c), entry[1])

    def test_inclusion_tag_errors(self):
        errors = [
            ("'inclusion_one_default' received unexpected keyword argument 'three'",
                '{% load inclusion %}{% inclusion_one_default 99 two="hello" three="foo" %}'),
            ("'inclusion_two_params' received too many positional arguments",
                '{% load inclusion %}{% inclusion_two_params 37 42 56 %}'),
            ("'inclusion_one_default' received too many positional arguments",
                '{% load inclusion %}{% inclusion_one_default 37 42 56 %}'),
            ("'inclusion_one_default' did not receive value(s) for the argument(s): 'one'",
                '{% load inclusion %}{% inclusion_one_default %}'),
            ("'inclusion_unlimited_args' did not receive value(s) for the argument(s): 'one'",
                '{% load inclusion %}{% inclusion_unlimited_args %}'),
            (
                "'inclusion_unlimited_args_kwargs' received some positional argument(s) "
                "after some keyword argument(s)",
                '{% load inclusion %}{% inclusion_unlimited_args_kwargs 37 40|add:2 eggs="boiled" 56 four=1|add:3 %}',
            ),
            ("'inclusion_unlimited_args_kwargs' received multiple values for keyword argument 'eggs'",
                '{% load inclusion %}{% inclusion_unlimited_args_kwargs 37 eggs="scrambled" eggs="scrambled" %}'),
        ]

        for entry in errors:
            with self.assertRaisesMessage(TemplateSyntaxError, entry[0]):
                Template(entry[1])

    def test_include_tag_missing_context(self):
        # The 'context' parameter must be present when takes_context is True
        msg = (
            "'inclusion_tag_without_context_parameter' is decorated with "
            "takes_context=True so it must have a first argument of 'context'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template('{% load inclusion %}{% inclusion_tag_without_context_parameter 123 %}')

    def test_inclusion_tags_from_template(self):
        c = Context({'value': 42})

        templates = [
            ('{% load inclusion %}{% inclusion_no_params_from_template %}',
                'inclusion_no_params_from_template - Expected result\n'),
            ('{% load inclusion %}{% inclusion_one_param_from_template 37 %}',
                'inclusion_one_param_from_template - Expected result: 37\n'),
            ('{% load inclusion %}{% inclusion_explicit_no_context_from_template 37 %}',
                'inclusion_explicit_no_context_from_template - Expected result: 37\n'),
            ('{% load inclusion %}{% inclusion_no_params_with_context_from_template %}',
                'inclusion_no_params_with_context_from_template - Expected result (context value: 42)\n'),
            ('{% load inclusion %}{% inclusion_params_and_context_from_template 37 %}',
                'inclusion_params_and_context_from_template - Expected result (context value: 42): 37\n'),
            ('{% load inclusion %}{% inclusion_two_params_from_template 37 42 %}',
                'inclusion_two_params_from_template - Expected result: 37, 42\n'),
            ('{% load inclusion %}{% inclusion_one_default_from_template 37 %}',
                'inclusion_one_default_from_template - Expected result: 37, hi\n'),
            ('{% load inclusion %}{% inclusion_one_default_from_template 37 42 %}',
                'inclusion_one_default_from_template - Expected result: 37, 42\n'),
            ('{% load inclusion %}{% inclusion_unlimited_args_from_template 37 %}',
                'inclusion_unlimited_args_from_template - Expected result: 37, hi\n'),
            ('{% load inclusion %}{% inclusion_unlimited_args_from_template 37 42 56 89 %}',
                'inclusion_unlimited_args_from_template - Expected result: 37, 42, 56, 89\n'),
            ('{% load inclusion %}{% inclusion_only_unlimited_args_from_template %}',
                'inclusion_only_unlimited_args_from_template - Expected result: \n'),
            ('{% load inclusion %}{% inclusion_only_unlimited_args_from_template 37 42 56 89 %}',
                'inclusion_only_unlimited_args_from_template - Expected result: 37, 42, 56, 89\n'),
        ]

        for entry in templates:
            t = Template(entry[0])
            self.assertEqual(t.render(c), entry[1])

    def test_inclusion_tag_registration(self):
        # Test that the decorators preserve the decorated function's docstring, name and attributes.
        self.verify_tag(inclusion.inclusion_no_params, 'inclusion_no_params')
        self.verify_tag(inclusion.inclusion_one_param, 'inclusion_one_param')
        self.verify_tag(inclusion.inclusion_explicit_no_context, 'inclusion_explicit_no_context')
        self.verify_tag(inclusion.inclusion_no_params_with_context, 'inclusion_no_params_with_context')
        self.verify_tag(inclusion.inclusion_params_and_context, 'inclusion_params_and_context')
        self.verify_tag(inclusion.inclusion_two_params, 'inclusion_two_params')
        self.verify_tag(inclusion.inclusion_one_default, 'inclusion_one_default')
        self.verify_tag(inclusion.inclusion_unlimited_args, 'inclusion_unlimited_args')
        self.verify_tag(inclusion.inclusion_only_unlimited_args, 'inclusion_only_unlimited_args')
        self.verify_tag(inclusion.inclusion_tag_without_context_parameter, 'inclusion_tag_without_context_parameter')
        self.verify_tag(inclusion.inclusion_tag_use_l10n, 'inclusion_tag_use_l10n')
        self.verify_tag(inclusion.inclusion_tag_current_app, 'inclusion_tag_current_app')
        self.verify_tag(inclusion.inclusion_unlimited_args_kwargs, 'inclusion_unlimited_args_kwargs')

    @ignore_warnings(category=RemovedInDjango20Warning)
    def test_15070_current_app(self):
        """
        Test that inclusion tag passes down `current_app` of context to the
        Context of the included/rendered template as well.
        """
        c = Context({})
        t = Template('{% load inclusion %}{% inclusion_tag_current_app %}')
        self.assertEqual(t.render(c).strip(), 'None')

        # That part produces the deprecation warning
        c = Context({}, current_app='advanced')
        self.assertEqual(t.render(c).strip(), 'advanced')

    def test_15070_use_l10n(self):
        """
        Test that inclusion tag passes down `use_l10n` of context to the
        Context of the included/rendered template as well.
        """
        c = Context({})
        t = Template('{% load inclusion %}{% inclusion_tag_use_l10n %}')
        self.assertEqual(t.render(c).strip(), 'None')

        c.use_l10n = True
        self.assertEqual(t.render(c).strip(), 'True')

    def test_no_render_side_effect(self):
        """
        #23441 -- InclusionNode shouldn't modify its nodelist at render time.
        """
        engine = Engine(app_dirs=True)
        template = engine.from_string('{% load inclusion %}{% inclusion_no_params %}')
        count = template.nodelist.get_nodes_by_type(Node)
        template.render(Context({}))
        self.assertEqual(template.nodelist.get_nodes_by_type(Node), count)

    def test_render_context_is_cleared(self):
        """
        #24555 -- InclusionNode should push and pop the render_context stack
        when rendering. Otherwise, leftover values such as blocks from
        extending can interfere with subsequent rendering.
        """
        engine = Engine(app_dirs=True)
        template = engine.from_string('{% load inclusion %}{% inclusion_extends1 %}{% inclusion_extends2 %}')
        self.assertEqual(template.render(Context({})).strip(), 'one\ntwo')


class AssignmentTagTests(TagTestCase):

    def test_assignment_tags(self):
        c = Context({'value': 42})

        t = Template('{% load custom %}{% assignment_no_params as var %}The result is: {{ var }}')
        self.assertEqual(t.render(c), 'The result is: assignment_no_params - Expected result')

    def test_assignment_tag_registration(self):
        # Test that the decorators preserve the decorated function's docstring, name and attributes.
        self.verify_tag(custom.assignment_no_params, 'assignment_no_params')

    def test_assignment_tag_missing_context(self):
        # The 'context' parameter must be present when takes_context is True
        msg = (
            "'assignment_tag_without_context_parameter' is decorated with "
            "takes_context=True so it must have a first argument of 'context'"
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template('{% load custom %}{% assignment_tag_without_context_parameter 123 as var %}')


class TemplateTagLoadingTests(SimpleTestCase):

    def setUp(self):
        self.egg_dir = os.path.join(ROOT, 'eggs')

    def test_load_error(self):
        ttext = "{% load broken_tag %}"
        with self.assertRaises(TemplateSyntaxError) as e:
            Template(ttext)

        self.assertIn('ImportError', e.exception.args[0])
        self.assertIn('Xtemplate', e.exception.args[0])

    def test_load_error_egg(self):
        ttext = "{% load broken_egg %}"
        egg_name = '%s/tagsegg.egg' % self.egg_dir
        with extend_sys_path(egg_name):
            with self.assertRaises(TemplateSyntaxError):
                with self.settings(INSTALLED_APPS=['tagsegg']):
                    Template(ttext)
            try:
                with self.settings(INSTALLED_APPS=['tagsegg']):
                    Template(ttext)
            except TemplateSyntaxError as e:
                self.assertIn('ImportError', e.args[0])
                self.assertIn('Xtemplate', e.args[0])

    def test_load_working_egg(self):
        ttext = "{% load working_egg %}"
        egg_name = '%s/tagsegg.egg' % self.egg_dir
        with extend_sys_path(egg_name):
            with self.settings(INSTALLED_APPS=['tagsegg']):
                Template(ttext)
