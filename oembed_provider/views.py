import re

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse, get_resolver
from django.http import HttpResponseBadRequest, Http404
# from django.template import defaultfilters, RequestContext
from django.utils.encoding import smart_str

from .sites import site
# from .consumer import OEmbedConsumer
from .exceptions import OEmbedException, OEmbedMissingEndpoint
from .providers import DjangoProvider, HTTPProvider
from . import mixins


resolver = get_resolver(None)


class OembedResourceView(mixins.JSONResponseMixin, mixins.BaseJsonDetailView):

    """
    The oembed endpoint, or the url to which requests for metadata are passed.
    Third parties will want to access this view with URLs for your site's
    content and be returned OEmbed metadata.
    """
    resource = None
    callback = None

    def get_object(self, request, *args, **kwargs):
        # coerce to dictionary
        params = dict(self.request.GET.items())

        self.callback = params.pop('callback', None)
        url = params.pop('url', None)

        if not url:
            self.response_class = HttpResponseBadRequest(
                'Required parameter missing: URL')
            return None

        try:
            provider = site.provider_for_url(url)
            if not provider.provides:
                raise OEmbedMissingEndpoint()
        except OEmbedMissingEndpoint:
            raise Http404('No provider found for %s' % url)

        query = dict([(smart_str(k), smart_str(v))
                     for k, v in params.items() if v])

        try:
            self.resource = site.embed(url, **query)
        except OEmbedException as error:
            raise Http404('Error embedding %s: %s' % (url, str(error)))

    def get_context_data(self, **kwargs):
        if self.callback:
            return '{callback}({json})'.format(
                callback=defaultfilters.force_escape(self.callback),
                json=self.resource.json)
        else:
            return self.resource.json


# class OembedConsumeJsonView(mixins.JSONResponseMixin, View):
#     """
#     Extract and return oembed content for given urls.

#     Required GET params:
#         urls - list of urls to consume

#     Optional GET params:
#         width - maxwidth attribute for oembed content
#         height - maxheight attribute for oembed content
#         template_dir - template_dir to use when rendering oembed

#     Returns:
#         list of dictionaries with oembed metadata and renderings, json encoded
#     """
#     def render_to_response():
#         client = OEmbedConsumer()

#         urls = request.GET.getlist('urls')
#         width = request.GET.get('width')
#         height = request.GET.get('height')
#         template_dir = request.GET.get('template_dir')

#         output = {}
#         ctx = RequestContext(request)

#         for url in urls:
#             try:
#                 provider = site.provider_for_url(url)
#             except OEmbedMissingEndpoint:
#                 oembeds = None
#                 rendered = None
#             else:
#                 oembeds = url
#                 rendered = client.parse_text(
# url, width, height, context=ctx, template_dir=template_dir)

#             output[url] = {
#                 'oembeds': oembeds,
#                 'rendered': rendered,
#             }

#         return HttpResponse(json.dumps(output), mimetype='application/json')


class OembedSchemaView(mixins.JSONResponseMixin, mixins.BaseJsonDetailView):

    """
    A site profile detailing valid endpoints for a given domain.  Allows for
    better auto-discovery of embeddable content.

    OEmbed-able content lives at a URL that maps to a provider.
    """
    sort_key = 'matches'

    def sort_scheme(self, schemes):
        return schemes.sort(key=lambda item: item.get(self.sort_key))

    def get_context_data(self, request, *args, **kwargs):
        output = []
        current_domain = Site.objects.get_current().domain
        endpoint = reverse('oembed_json')
                           # the public endpoint for our oembeds
        providers = site.get_providers()

        for provider in providers:
            # first make sure this provider class is exposed at the public
            # endpoint
            if not provider.provides:
                continue

            match = None
            if isinstance(provider, DjangoProvider):
                path_regex = provider._path_regex()

                # this regex replacement is set to be non-greedy, which results
                # in things like /news/*/*/*/*/ -- this is more explicit
                if path_regex:
                    regex = re.sub(r'%\(.+?\)s', '*', path_regex)
                    match = 'http://%s/%s' % (current_domain, regex)

            elif isinstance(provider, HTTPProvider):
                match = provider.url_scheme

            else:
                match = provider.regex

            if match:
                output.append({
                    'type': provider.resource_type,
                    'matches': match,
                    'endpoint': endpoint
                })

        return self.sort_scheme(output)
