{ config, pkgs, ... }:

let
  markerFile = "/var/lib/lnbits/.configured";
  caddyfile = "/var/lib/caddy/Caddyfile";
  certFile = "/var/lib/caddy/cert.pem";
  keyFile = "/var/lib/caddy/key.pem";

  # Script to generate self-signed cert if it doesn't exist
  generate-caddy-cert = pkgs.writeShellScript "generate-caddy-cert" ''
    if [ ! -f ${certFile} ] || [ ! -f ${keyFile} ]; then
      ${pkgs.openssl}/bin/openssl req -x509 \
        -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
        -keyout ${keyFile} -out ${certFile} \
        -days 3650 -nodes \
        -subj '/CN=LNbitsBox' \
        -addext 'subjectAltName=DNS:lnbits,DNS:lnbits.local,DNS:localhost,IP:127.0.0.1'
    fi
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
      '	handle /box/* {' \
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
      '	redir https://{host}{uri} permanent' \
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

  # Open ports 80 (redirect) and 443 (HTTPS) in firewall
  networking.firewall.allowedTCPPorts = [ 80 443 ];
}
