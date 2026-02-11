{ config, pkgs, ... }:

let
  markerFile = "/var/lib/lnbits/.configured";
  caddyfile = "/var/lib/caddy/Caddyfile";
  caCertFile = "/var/lib/caddy/ca-cert.pem";
  caKeyFile = "/var/lib/caddy/ca-key.pem";
  certFile = "/var/lib/caddy/cert.pem";
  keyFile = "/var/lib/caddy/key.pem";
  certTrustPage = ./cert-trust-page;

  # Script to generate Root CA (once) and server cert (each boot with current IP)
  generate-caddy-cert = pkgs.writeShellScript "generate-caddy-cert" ''
    OPENSSL=${pkgs.openssl}/bin/openssl
    IP_CMD=${pkgs.iproute2}/bin/ip

    # Phase 1: Root CA — generated ONCE, persists across reboots
    if [ ! -f ${caCertFile} ] || [ ! -f ${caKeyFile} ]; then
      echo "Generating LNbitsBox Root CA..."
      $OPENSSL req -x509 \
        -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
        -keyout ${caKeyFile} -out ${caCertFile} \
        -days 3650 -nodes \
        -subj '/CN=LNbitsBox Root CA'
      chmod 644 ${caCertFile}
      chmod 600 ${caKeyFile}
    fi

    # Phase 2: Server cert — regenerated each boot to pick up IP changes
    echo "Generating server certificate..."
    CURRENT_IP=$($IP_CMD -4 route get 1.1.1.1 2>/dev/null | ${pkgs.gawk}/bin/awk '{for(i=1;i<=NF;i++) if ($i=="src") print $(i+1)}')
    SAN="DNS:lnbits,DNS:lnbits.local,DNS:localhost,IP:127.0.0.1"
    [ -n "$CURRENT_IP" ] && SAN="$SAN,IP:$CURRENT_IP"

    # Generate CSR
    $OPENSSL req -new \
      -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
      -keyout ${keyFile} -out /tmp/server.csr -nodes \
      -subj '/CN=LNbitsBox' \
      -addext "subjectAltName=$SAN"

    # Sign with Root CA
    $OPENSSL x509 -req \
      -in /tmp/server.csr \
      -CA ${caCertFile} -CAkey ${caKeyFile} -CAcreateserial \
      -out ${certFile} \
      -days 825 -copy_extensions copyall

    rm -f /tmp/server.csr
    chmod 644 ${certFile}
    chmod 600 ${keyFile}
  '';

  # Script to generate Caddyfile based on system state
  generate-caddy-config = pkgs.writeShellScript "generate-caddy-config" ''
    if [ -f ${markerFile} ]; then
      BACKEND="127.0.0.1:5000"
    else
      BACKEND="127.0.0.1:8080"
    fi

    printf '%s\n' \
      '{' \
      '	log {' \
      '		output discard' \
      '	}' \
      '}' \
      "" \
      'https:// {' \
      '	tls ${certFile} ${keyFile}' \
      "" \
      '	handle /health {' \
      '		respond "ok" 200' \
      '	}' \
      "" \
      '	@box-redir path /box' \
      '	redir @box-redir /box/ 308' \
      "" \
      '	@box path /box/*' \
      '	handle @box {' \
      '		reverse_proxy 127.0.0.1:8090' \
      '	}' \
      "" \
      '	handle {' \
      "		reverse_proxy $BACKEND {" \
      '			transport http {' \
      '				read_timeout 300s' \
      '				write_timeout 300s' \
      '			}' \
      '		}' \
      '	}' \
      '}' \
      "" \
      'http:// {' \
      '	handle /cert/download {' \
      '		header Content-Disposition "attachment; filename=\"LNbitsBox-CA.crt\""' \
      '		header Content-Type "application/x-x509-ca-cert"' \
      '		rewrite * /ca-cert.pem' \
      '		root * /var/lib/caddy' \
      '		file_server' \
      '	}' \
      '	handle /health {' \
      '		respond "ok" 200' \
      '	}' \
      '	handle {' \
      '		root * ${certTrustPage}' \
      '		try_files {path} /index.html' \
      '		file_server' \
      '	}' \
      '}' \
      > ${caddyfile}
  '';

  # Script to regenerate config and reload Caddy
  reload-caddy-config = pkgs.writeShellScript "reload-caddy-config" ''
    ${generate-caddy-config}
    ${pkgs.caddy}/bin/caddy reload --config ${caddyfile} --force 2>/dev/null || true
  '';
in
{
  # Make reload script available system-wide (used by configurator and reset)
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "reload-caddy-config" ''
      ${generate-caddy-config}
      ${pkgs.caddy}/bin/caddy reload --config ${caddyfile} --force 2>/dev/null || true
    '')
  ];

  services.caddy = {
    enable = true;
    # Dummy config — overridden by ExecStartPre
    globalConfig = "";
  };

  # Override Caddy systemd service to use dynamic Caddyfile
  systemd.services.caddy = {
    wants = [ "network-online.target" ];
    after = [ "network-online.target" ];

    serviceConfig = {
      # Generate cert and Caddyfile before Caddy starts
      ExecStartPre = [
        ""  # Clear default ExecStartPre
        "${generate-caddy-cert}"
        "${generate-caddy-config}"
      ];
      ExecStart = [
        ""  # Clear default ExecStart
        "${pkgs.caddy}/bin/caddy run --config ${caddyfile}"
      ];
      ExecReload = [
        ""  # Clear default ExecReload
        "${reload-caddy-config}"
      ];
    };
  };

  # Open ports 80 (cert trust page) and 443 (HTTPS) in firewall
  networking.firewall.allowedTCPPorts = [ 80 443 ];
}
