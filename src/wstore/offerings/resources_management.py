import base64
import os

from django.conf import settings

from wstore.models import Resource


def register_resource(provider, data, file_=None):

    # Check if the resource already exists
    existing = True
    try:
        Resource.objects.get(name=data['name'], provider=provider, version=data['version'])
    except:
        existing = False

    if existing:
        raise Exception('The resource already exists')

    resource_data = {
        'name': data['name'],
        'version': data['version'],
        'type': 'download',
        'description': data['description'],
        'content_type': data['content_type']
    }

    if file_ is None:
        if 'content' in data:
            resource = data['content']

            #decode the content and save the media file
            file_name = provider.username + '__' + data['name'] + '__' + data['version'] + '__' + resource['name']
            path = os.path.join(settings.MEDIA_ROOT, 'resources')
            file_path = os.path.join(path, file_name)
            f = open(file_path, "wb")
            dec = base64.b64decode(resource['data'])
            f.write(dec)
            f.close()
            resource_data['content_path'] = settings.MEDIA_URL + 'resources/' + file_name
            resource_data['link'] = ''

        elif 'link' in data:
            # Add the download link
            resource_data['link'] = data['link']
            resource_data['content_path'] = ''

    else:
        #decode the content and save the media file
        file_name = provider.username + '__' + data['name'] + '__' + data['version'] + '__' + file_.name
        path = os.path.join(settings.MEDIA_ROOT, 'resources')
        file_path = os.path.join(path, file_name)
        f = open(file_path, "wb")
        f.write(file_.read())
        f.close()
        resource_data['content_path'] = settings.MEDIA_URL + 'resources/' + file_name
        resource_data['link'] = ''

    Resource.objects.create(
        name=resource_data['name'],
        provider=provider,
        version=resource_data['version'],
        resource_type=resource_data['type'],
        description=resource_data['description'],
        download_link=resource_data['link'],
        resource_path=resource_data['content_path'],
        content_type=resource_data['content_type']
    )


def get_provider_resources(provider):
    resouces = Resource.objects.filter(provider=provider)
    response = []
    for res in resouces:
        response.append({
            'name': res.name,
            'version': res.version,
            'description': res.description,
            'content_type': res.content_type
        })

    return response
