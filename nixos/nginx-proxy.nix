{ config, pkgs, ... }:

{
  services.nginx = {
    enable = true;

    recommendedProxySettings = true;
    recommendedTlsSettings = true;
    recommendedOptimisation = true;
    recommendedGzipSettings = true;

    virtualHosts."lnbitspi" = {
      default = true;
      listen = [
        { addr = "0.0.0.0"; port = 80; }
      ];

      # Disable access logs to prevent mnemonic leakage
      extraConfig = ''
        access_log off;
        error_log /var/log/nginx/error.log error;
      '';

      locations."/box/" = {
        extraConfig = ''
          proxy_pass http://127.0.0.1:8090;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
        '';
      };

      locations."/" = {
        extraConfig = ''
          # Default to configurator (unconfigured state)
          set $backend "http://127.0.0.1:8080";

          # If configured, route to LNbits
          if (-f /var/lib/lnbits/.configured) {
            set $backend "http://127.0.0.1:5000";
          }

          proxy_pass $backend;
          proxy_http_version 1.1;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;

          # Timeouts
          proxy_read_timeout 300;
          proxy_connect_timeout 300;
          proxy_send_timeout 300;
        '';
      };
    };
  };

  # Ensure nginx starts early
  systemd.services.nginx.wants = [ "network-online.target" ];
  systemd.services.nginx.after = [ "network-online.target" ];

  # Open port 80 in firewall (already done in configuration.nix, but be explicit)
  networking.firewall.allowedTCPPorts = [ 80 ];
}
