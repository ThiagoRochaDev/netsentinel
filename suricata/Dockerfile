FROM jasonish/suricata:7.0.7

COPY suricata.yaml /etc/suricata/suricata.yaml.template
COPY rules/local.rules /etc/suricata/local-rules/local.rules
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
