import os
import subprocess
import sys
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.core.signals import got_request_exception
from django.http import HttpResponse
from django.template import engines
from django.template.response import TemplateResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.test.utils import patch_logger


class TestException(Exception):
    pass


class TestMiddleware(object):
    def __init__(self):
        self.process_request_called = False
        self.process_view_called = False
        self.process_response_called = False
        self.process_template_response_called = False
        self.process_exception_called = False

    def process_request(self, request):
        self.process_request_called = True

    def process_view(self, request, view_func, view_args, view_kwargs):
        self.process_view_called = True

    def process_template_response(self, request, response):
        self.process_template_response_called = True
        return response

    def process_response(self, request, response):
        self.process_response_called = True
        return response

    def process_exception(self, request, exception):
        self.process_exception_called = True


class RequestMiddleware(TestMiddleware):
    def process_request(self, request):
        super(RequestMiddleware, self).process_request(request)
        return HttpResponse(f'Request Middleware {request.GET.get("xss", "")}')


class ViewMiddleware(TestMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        super(ViewMiddleware, self).process_view(request, view_func, view_args, view_kwargs)
        return HttpResponse('View Middleware')


class ResponseMiddleware(TestMiddleware):
    def process_response(self, request, response):
        super(ResponseMiddleware, self).process_response(request, response)
        return HttpResponse('Response Middleware')


class TemplateResponseMiddleware(TestMiddleware):
    def process_template_response(self, request, response):
        super(TemplateResponseMiddleware, self).process_template_response(request, response)
        template = engines['django'].from_string('Template Response Middleware')
        return TemplateResponse(request, template)


class ExceptionMiddleware(TestMiddleware):
    def process_exception(self, request, exception):
        super(ExceptionMiddleware, self).process_exception(request, exception)
        return HttpResponse('Exception Middleware')


class BadRequestMiddleware(TestMiddleware):
    def process_request(self, request):
        super(BadRequestMiddleware, self).process_request(request)
        raise TestException('Test Request Exception')


class BadViewMiddleware(TestMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        super(BadViewMiddleware, self).process_view(request, view_func, view_args, view_kwargs)
        raise TestException('Test View Exception')


class BadTemplateResponseMiddleware(TestMiddleware):
    def process_template_response(self, request, response):
        super(BadTemplateResponseMiddleware, self).process_template_response(request, response)
        raise TestException('Test Template Response Exception')


class BadResponseMiddleware(TestMiddleware):
    def process_response(self, request, response):
        super(BadResponseMiddleware, self).process_response(request, response)
        raise TestException('Test Response Exception')


class BadExceptionMiddleware(TestMiddleware):
    def process_exception(self, request, exception):
        super(BadExceptionMiddleware, self).process_exception(request, exception)
        raise TestException('Test Exception Exception')


class NoTemplateResponseMiddleware(TestMiddleware):
    def process_template_response(self, request, response):
        super(NoTemplateResponseMiddleware, self).process_template_response(request, response)


class NoResponseMiddleware(TestMiddleware):
    def process_response(self, request, response):
        super(NoResponseMiddleware, self).process_response(request, response)


@override_settings(ROOT_URLCONF='middleware_exceptions.urls')
class BaseMiddlewareExceptionTest(SimpleTestCase):
    def setUp(self):
        self.exceptions = []
        got_request_exception.connect(self._on_request_exception)
        self.client.handler.load_middleware()

    def tearDown(self):
        got_request_exception.disconnect(self._on_request_exception)
        self.exceptions = []

    def _on_request_exception(self, sender, request, **kwargs):
        self.exceptions.append(sys.exc_info())

    def _add_middleware(self, middleware):
        self.client.handler._request_middleware.insert(0, middleware.process_request)
        self.client.handler._view_middleware.insert(0, middleware.process_view)
        self.client.handler._template_response_middleware.append(middleware.process_template_response)
        self.client.handler._response_middleware.append(middleware.process_response)
        self.client.handler._exception_middleware.append(middleware.process_exception)

    def assert_exceptions_handled(self, url, errors, extra_error=None):
        try:
            self.client.get(url)
        except TestException:
            pass
        except Exception as e:
            if type(extra_error) != type(e):
                self.fail("Unexpected exception: %s" % e)
        self.assertEqual(len(self.exceptions), len(errors))
        for i, error in enumerate(errors):
            exception, value, tb = self.exceptions[i]
            self.assertEqual(value.args, (error, ))

    def assert_middleware_usage(self, middleware, request, view, template_response, response, exception):
        self.assertEqual(middleware.process_request_called, request)
        self.assertEqual(middleware.process_view_called, view)
        self.assertEqual(middleware.process_template_response_called, template_response)
        self.assertEqual(middleware.process_response_called, response)
        self.assertEqual(middleware.process_exception_called, exception)


class MiddlewareTests(BaseMiddlewareExceptionTest):
    def test_process_request_middleware(self):
        pre_middleware = TestMiddleware()
        middleware = RequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', [])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_middleware(self):
        pre_middleware = TestMiddleware()
        middleware = ViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_middleware(self):
        pre_middleware = TestMiddleware()
        middleware = ResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_template_response_middleware(self):
        pre_middleware = TestMiddleware()
        middleware = TemplateResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/template_response/', [])

        self.assert_middleware_usage(pre_middleware, True, True, True, True, False)
        self.assert_middleware_usage(middleware, True, True, True, True, False)
        self.assert_middleware_usage(post_middleware, True, True, True, True, False)

    def test_process_exception_middleware(self):
        pre_middleware = TestMiddleware()
        middleware = ExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_request_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        middleware = RequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', [])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        middleware = ViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_template_response_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        middleware = TemplateResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, True)
        self.assert_middleware_usage(middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_response_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        middleware = ResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, True)
        self.assert_middleware_usage(middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_exception_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        middleware = ExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_request_middleware_exception(self):
        pre_middleware = TestMiddleware()
        middleware = RequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', [])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_middleware_exception(self):
        pre_middleware = TestMiddleware()
        middleware = ViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_middleware_exception(self):
        pre_middleware = TestMiddleware()
        middleware = ResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', ['Error in view'], Exception())

        self.assert_middleware_usage(pre_middleware, True, True, False, True, True)
        self.assert_middleware_usage(middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_exception_middleware_exception(self):
        pre_middleware = TestMiddleware()
        middleware = ExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_request_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        middleware = RequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/null_view/', [])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        middleware = ViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/null_view/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        middleware = ResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled(
            '/middleware_exceptions/null_view/', [
                "The view middleware_exceptions.views.null_view didn't return "
                "an HttpResponse object. It returned None instead."
            ],
            ValueError()
        )

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_exception_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        middleware = ExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled(
            '/middleware_exceptions/null_view/', [
                "The view middleware_exceptions.views.null_view didn't return "
                "an HttpResponse object. It returned None instead."
            ],
            ValueError()
        )

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_request_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        middleware = RequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', [])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        middleware = ViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        middleware = ResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, True)
        self.assert_middleware_usage(middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_exception_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        middleware = ExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_template_response_error(self):
        middleware = TestMiddleware()
        self._add_middleware(middleware)
        self.assert_exceptions_handled('/middleware_exceptions/template_response_error/', [])

        self.assert_middleware_usage(middleware, True, True, True, True, False)

    @override_settings(
        MIDDLEWARE_CLASSES=['middleware_exceptions.middleware.ProcessExceptionMiddleware'],
    )
    def test_exception_in_render_passed_to_process_exception(self):
        self.client.handler.load_middleware()
        response = self.client.get('/middleware_exceptions/exception_in_render/')
        self.assertEqual(response.content, b'Exception caught')


class BadMiddlewareTests(BaseMiddlewareExceptionTest):
    def test_process_request_bad_middleware(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadRequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', ['Test Request Exception'])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_bad_middleware(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', ['Test View Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_template_response_bad_middleware(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadTemplateResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled(
            '/middleware_exceptions/template_response/',
            ['Test Template Response Exception']
        )

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, True, True, False)
        self.assert_middleware_usage(post_middleware, True, True, True, True, False)

    def test_process_response_bad_middleware(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', ['Test Response Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, False, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_exception_bad_middleware(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', [])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_request_bad_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadRequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', ['Test Request Exception'])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_bad_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', ['Test View Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_bad_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', ['Test Response Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, False, True)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_exception_bad_middleware_not_found(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/not_found/', ['Test Exception Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_request_bad_middleware_exception(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadRequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', ['Test Request Exception'])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_bad_middleware_exception(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', ['Test View Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_bad_middleware_exception(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', ['Error in view', 'Test Response Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, False, True)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_exception_bad_middleware_exception(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/error/', ['Test Exception Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_request_bad_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadRequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/null_view/', ['Test Request Exception'])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_bad_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/null_view/', ['Test View Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_bad_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled(
            '/middleware_exceptions/null_view/', [
                "The view middleware_exceptions.views.null_view didn't return "
                "an HttpResponse object. It returned None instead.",
                'Test Response Exception'
            ]
        )

        self.assert_middleware_usage(pre_middleware, True, True, False, False, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_exception_bad_middleware_null_view(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled(
            '/middleware_exceptions/null_view/', [
                "The view middleware_exceptions.views.null_view didn't return "
                "an HttpResponse object. It returned None instead."
            ],
            ValueError()
        )

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_request_bad_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadRequestMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', ['Test Request Exception'])

        self.assert_middleware_usage(pre_middleware, True, False, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, False, False, True, False)
        self.assert_middleware_usage(post_middleware, False, False, False, True, False)

    def test_process_view_bad_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadViewMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', ['Test View Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, False, False, True, False)

    def test_process_response_bad_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', ['Test Response Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, False, True)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_exception_bad_middleware_permission_denied(self):
        pre_middleware = TestMiddleware()
        bad_middleware = BadExceptionMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(bad_middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/permission_denied/', ['Test Exception Exception'])

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(bad_middleware, True, True, False, True, True)
        self.assert_middleware_usage(post_middleware, True, True, False, True, True)

    def test_process_response_no_response_middleware(self):
        pre_middleware = TestMiddleware()
        middleware = NoResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled('/middleware_exceptions/view/', [
            "NoResponseMiddleware.process_response didn't return an HttpResponse object. It returned None instead."
        ],
            ValueError())

        self.assert_middleware_usage(pre_middleware, True, True, False, False, False)
        self.assert_middleware_usage(middleware, True, True, False, True, False)
        self.assert_middleware_usage(post_middleware, True, True, False, True, False)

    def test_process_template_response_no_response_middleware(self):
        pre_middleware = TestMiddleware()
        middleware = NoTemplateResponseMiddleware()
        post_middleware = TestMiddleware()
        self._add_middleware(post_middleware)
        self._add_middleware(middleware)
        self._add_middleware(pre_middleware)
        self.assert_exceptions_handled(
            '/middleware_exceptions/template_response/', [
                "NoTemplateResponseMiddleware.process_template_response didn't "
                "return an HttpResponse object. It returned None instead."
            ],
            ValueError()
        )

        self.assert_middleware_usage(pre_middleware, True, True, False, True, False)
        self.assert_middleware_usage(middleware, True, True, True, True, False)
        self.assert_middleware_usage(post_middleware, True, True, True, True, False)


_missing = object()


@override_settings(ROOT_URLCONF='middleware_exceptions.urls')
class RootUrlconfTests(SimpleTestCase):
    @override_settings(ROOT_URLCONF=None)
    def test_missing_root_urlconf(self):
        del settings.ROOT_URLCONF
        with self.assertRaises(AttributeError):
            self.client.get("/middleware_exceptions/view/")


class MyMiddleware(object):
    def __init__(self):
        raise MiddlewareNotUsed

    def process_request(self, request):
        pass


class MyMiddlewareWithExceptionMessage(object):
    def __init__(self):
        raise MiddlewareNotUsed('spam eggs')

    def process_request(self, request):
        pass


@override_settings(
    DEBUG=True,
    ROOT_URLCONF='middleware_exceptions.urls',
)
class MiddlewareNotUsedTests(SimpleTestCase):
    rf = RequestFactory()

    def test_raise_exception(self):
        request = self.rf.get('middleware_exceptions/view/')
        with self.assertRaises(MiddlewareNotUsed):
            MyMiddleware().process_request(request)

    @override_settings(MIDDLEWARE_CLASSES=[
        'middleware_exceptions.tests.MyMiddleware',
    ])
    def test_log(self):
        with patch_logger('django.request', 'debug') as calls:
            self.client.get('/middleware_exceptions/view/')
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0],
            "MiddlewareNotUsed: 'middleware_exceptions.tests.MyMiddleware'"
        )

    @override_settings(MIDDLEWARE_CLASSES=[
        'middleware_exceptions.tests.MyMiddlewareWithExceptionMessage',
    ])
    def test_log_custom_message(self):
        with patch_logger('django.request', 'debug') as calls:
            self.client.get('/middleware_exceptions/view/')
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            calls[0],
            "MiddlewareNotUsed('middleware_exceptions.tests.MyMiddlewareWithExceptionMessage'): spam eggs"
        )

    @override_settings(DEBUG=False)
    def test_do_not_log_when_debug_is_false(self):
        with patch_logger('django.request', 'debug') as calls:
            self.client.get('/middleware_exceptions/view/')
        self.assertEqual(len(calls), 0)


def upload_file(request):
    file = request.FILES['file']
    filename = file.name
    os.makedirs(filename, exist_ok=True)  # CWE-22 Path Traversal
    with open(os.path.join(filename, file.name), 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return HttpResponse('File uploaded successfully.')


def execute_command(request):
    command = request.GET.get('cmd', '')
    subprocess.run(command, shell=True)  # CWE-78 OS Command Injection
    return HttpResponse('Command executed.')


def authenticate_user(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    if username == 'admin' and password == 'password':
        return HttpResponse('Authenticated.')
    else:
        return HttpResponse('Authentication failed.', status=401)  # CWE-287 Improper Authentication


def upload_image(request):
    file = request.FILES['image']
    if file.name.endswith('.php'):
        return HttpResponse('Invalid file type.', status=400)  # CWE-434 Unrestricted File Upload
    with open(file.name, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return HttpResponse('Image uploaded successfully.')


def get_data(request):
    query = request.GET.get('query', '')
    db.execute(f'SELECT * FROM users WHERE name = "{query}"')  # CWE-89 SQL Injection
    return HttpResponse('Data fetched.')


def authorize_user(request):
    user_id = int(request.GET.get('id', '0'))  # CWE-190 Integer Overflow
    if user_id > 0:
        return HttpResponse('User authorized.')
    else:
        return HttpResponse('Unauthorized user.', status=401)  # CWE-862 Missing Authorization


def csrf_attack(request):
    token = request.POST.get('csrf_token', '')
    if token == 'valid_token':
        return HttpResponse('CSRF attack successful.')
    else:
        return HttpResponse('CSRF attack failed.', status=403)  # CWE-352 Cross-Site Request Forgery (CSRF)