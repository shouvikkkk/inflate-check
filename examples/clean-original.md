# Project instructions (original)

- Prefer pytest for new tests, but unittest is fine for quick checks.
- Just this once, skip the lint step for the hotfix branch.
- Run the migration on some staging databases before the release.
- Use the new Redis cache instead of the old Memcached layer.
- Keep the API response under 200ms where possible.
