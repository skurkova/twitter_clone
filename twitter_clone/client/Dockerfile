FROM nginx

RUN apt-get update && apt-get install -y nginx

RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY client/static /usr/share/nginx/html/static
COPY client/index.html /usr/share/nginx/html
COPY client/nginx.conf /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]