"""Android registry routes must resolve; production callers must use the registry.

No database, Android toolchain or Kotlin execution is needed. This checks routing
and directly identifiable HTTP verbs, not DTOs, permissions or runtime behavior.
"""
import itertools
import re
from pathlib import Path
from unittest import skipUnless

from django.test import SimpleTestCase
from django.urls import resolve

from config.urls import api_not_found, spa_serve


ANDROID = Path(__file__).resolve().parents[3] / 'Android' / 'app' / 'src' / 'main' / 'java'
REGISTRY = ANDROID / 'com/mukhtabir/android/data/remote/ApiEndpoints.kt'
ROOT = r'(?:auth|questions|exam|study|recall|analytics|history|study-planner|database|admin|recovery|config|tips)'
STRING = re.compile(r'"([^"\n]*)"')
PLACEHOLDER = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z_]\w*)')


def source_text(path):
    source = re.sub(r'/\*.*?\*/', '', path.read_text(), flags=re.S)
    return re.sub(r'//[^\n]*', '', source)


def concrete_paths(template, source):
    variables = list(dict.fromkeys(m[1] or m[2] for m in PLACEHOLDER.finditer(template)))
    domains = {}
    for variable in variables:
        if variable == 'mode.path':
            enum = source.split('enum class TestMode', 1)[1]
            domains[variable] = re.findall(r'\w+\("([a-z]+)"\)', enum)
        elif variable == 'format':
            allowed = re.search(r'require\(format in setOf\(([^)]+)\)\)', source)
            domains[variable] = STRING.findall(allowed[1])
        elif variable == 'operation':
            domains[variable] = ['11111111-1111-4111-8111-111111111111']
        elif variable in {'id', 'user'}:
            domains[variable] = ['1']
        elif variable.startswith('android.net.Uri.encode('):
            domains[variable] = ['sample']
        else:
            raise AssertionError(f'Add an explicit sample domain for {variable!r}: {template}')
        if not domains[variable]:
            raise AssertionError(f'No samples extracted for {variable}')
    for values in itertools.product(*(domains[key] for key in variables)):
        substitutions = dict(zip(variables, values))
        yield PLACEHOLDER.sub(lambda m: substitutions[m[1] or m[2]], template)


@skipUnless(REGISTRY.exists(), 'Sibling Android checkout is required')
class AndroidEndpointContractTests(SimpleTestCase):
    def test_every_registry_path_resolves(self):
        source = source_text(REGISTRY)
        templates = {s for s in STRING.findall(source) if s.endswith('/') and (
            re.match(ROOT + '/', s) or s.startswith('${mode.path}/'))}
        self.assertGreater(len(templates), 100, 'Registry extraction stopped seeing routes')
        for template in sorted(templates):
            for path in concrete_paths(template, source):
                with self.subTest(template=template, path=path):
                    match = resolve('/api/v1/' + path)
                    self.assertNotIn(match.func, (api_not_found, spa_serve))

    def test_no_api_paths_outside_registry(self):
        for path in ANDROID.rglob('*.kt'):
            if path == REGISTRY:
                continue
            for literal in STRING.findall(source_text(path)):
                with self.subTest(file=str(path.relative_to(ANDROID)), literal=literal):
                    self.assertIsNone(re.fullmatch(ROOT + r'/[^\s]*', literal) if literal.endswith('/') else None,
                        'Move API paths into ApiEndpoints.kt')

    def test_direct_registry_call_methods_exist(self):
        source = source_text(REGISTRY)
        definitions = {}
        scope = ''
        for line in source.splitlines():
            nested = re.match(r'    object (\w+) \{', line)
            if nested:
                scope = nested[1] + '.'
            elif line == '    }':
                scope = ''
            definition = re.match(r'\s*(?:const val|fun) (\w+).*?= "([^"\n]+/)"$', line)
            if definition:
                definitions[scope + definition[1]] = definition[2]
        calls = re.compile(r'\bapi\.(get|post|put|delete|postMultipart|download)\(\s*ApiEndpoints\.([\w.]+)')
        checked = 0
        for path in ANDROID.rglob('*.kt'):
            for method, name in calls.findall(source_text(path)):
                if name not in definitions:
                    continue  # when-builders are covered by the route check above.
                verb = {'postMultipart': 'post', 'download': 'get'}.get(method, method)
                for endpoint in concrete_paths(definitions[name], source):
                    with self.subTest(file=path.name, endpoint=endpoint, method=verb):
                        view = resolve('/api/v1/' + endpoint).func.view_class
                        self.assertIn(verb, view.http_method_names)
                        self.assertTrue(callable(getattr(view, verb, None)))
                        checked += 1
        self.assertGreater(checked, 50, 'Method extraction stopped seeing callers')
