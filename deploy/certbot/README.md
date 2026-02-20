# Certbot / HTTPS (Fase 8)

Este projeto recomenda **Certbot no host** (Ubuntu) por simplicidade e previsibilidade.

## Opção A (recomendada) — Certbot no host com plugin Nginx

1) No servidor: aponte o DNS (A record) do seu domínio para o IP do servidor.

2) Libere portas no firewall:
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw status
```

3) Suba o stack em HTTP primeiro (para o Nginx responder na 80):
```bash
cd /opt/projeto01
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

4) Ajuste o `server_name` e paths no Nginx:
- Edite `deploy/nginx/default.conf` e substitua `SEU_DOMINIO` pelo domínio real.
- Reinicie o Nginx:
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod restart nginx
```

5) Instale o Certbot:
```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

6) Emita o certificado:
```bash
sudo certbot --nginx -d SEU_DOMINIO
```

7) Teste renovação:
```bash
sudo certbot renew --dry-run
```

> Observação: em Ubuntu, o Certbot normalmente instala um **systemd timer** automaticamente.

## Opção B (opcional) — Certbot em container (webroot)

Se você optar por containerizar, use volumes compartilhados:
- `/etc/letsencrypt` (certificados)
- `/var/www/certbot` (challenge webroot)

E garanta no Nginx:
- `location /.well-known/acme-challenge/ { root /var/www/certbot; }`

A Opção B dá mais trabalho e é mais sensível a detalhes, por isso a Opção A é a recomendada.
