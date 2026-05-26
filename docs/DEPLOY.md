# Deploy a PARALLAX-5 trust-surface registry

The trust-surface registry is what you'd host at `parallax5.io` (or your own domain) to serve Carfax-style reports for every protocol you cover.

## Locally (development)

```bash
parallax5 serve --dir ./certificates
# → http://localhost:8080
```

## Containerized

```bash
docker-compose up
# → http://localhost:8080
```

This serves every `.json` certificate in `./certificates/` as:

- `/` — index listing (sortable by tier/score)
- `/report/<name>` — Carfax-style HTML trust-surface report
- `/badge/<name>.svg` — embeddable SVG badge
- `/api/v1/cert/<name>` — raw certificate JSON
- `/api/v1/trust-surface/<name>` — derived trust-surface JSON

## Production (behind a reverse proxy)

The server uses Python's stdlib HTTP server. For production:

1. Run behind nginx or Caddy with TLS.
2. Mount `/certs` from your certificate publication pipeline.
3. Add basic auth or read-only access controls if needed.

Example nginx config:

```nginx
server {
  listen 443 ssl http2;
  server_name parallax5.io;
  ssl_certificate /etc/letsencrypt/live/parallax5.io/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/parallax5.io/privkey.pem;

  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

## Embedding badges

In your protocol's README:

```markdown
![PARALLAX-5](https://parallax5.io/badge/my-protocol.svg)
```

Renders as a shields.io-style pill: `PARALLAX-5 | B+ · P3`.
