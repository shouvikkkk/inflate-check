# Project instructions (compacted summary)

- Always use pytest for new tests; unittest is never allowed.
- Skip the lint step for the hotfix branch.
- Run the migration on all staging databases before the release.
- The Memcached layer is the current cache.
- Keep the API response under 200ms where possible.
