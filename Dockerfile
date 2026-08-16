# Sito statico servito da nginx. Nessun processo applicativo, nessun database:
# quello che esce dalla build e' una cartella di file, e questo container la
# serve e basta.
FROM nginx:1.27-alpine

COPY sito/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
