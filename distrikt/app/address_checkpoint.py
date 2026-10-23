"""Explicit source identity for resumable address downloads."""
REST_SOURCE = 'dar-rest-v3'
GRAPHQL_SOURCE = 'dar-graphql-v3'


def checkpoint_source(manifest):
    # All pre-migration checkpoints were created by the REST implementation.
    return manifest.get('source_id', REST_SOURCE)


def require_source(manifest, expected, schema=None):
    if (checkpoint_source(manifest) != expected or
            (expected == GRAPHQL_SOURCE and schema is not None and manifest.get('schema_sha256') != schema)):
        raise ValueError('Hentningen tilhører en anden adressekilde eller et ændret skema. Vælg en ny hentning/opdatering, eller gendan den tidligere forbindelse. Færdige lokale adresser er bevaret.')
