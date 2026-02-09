{ config, pkgs, ... }:

{
  services.tor = {
    enable = true;
    enableGeoIP = false;
    relay.onionServices.lnbits = {
      version = 3;
      map = [{
        port = 80;
        target = { addr = "127.0.0.1"; port = 5000; };
      }];
    };
  };
}
