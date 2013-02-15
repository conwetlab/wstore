
from fiware_store.models import Repository


def register_repository(name, host):

    # Check if the repository name is in use
    existing = True

    try:
        Repository.objects.get(name=name)
    except:
        existing = False

    if existing:
        raise Exception('The repository already exists')

    Repository.objects.create(name=name, host=host)


def unregister_repository(repository):
    rep = None
    try:
        rep = Repository.objects.get(name=repository)
    except:
        raise Exception('Not found')

    rep.delete()


def get_repositories():

    repositories = Repository.objects.all()
    response = []

    for rep in repositories:
        response.append({
            'name': rep.name,
            'host': rep.host
        })

    return response
