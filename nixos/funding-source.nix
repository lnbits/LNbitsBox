{ config, pkgs, ... }:

let
  stateDir = "/var/lib/lnbitsbox";
  selectedFile = "${stateDir}/funding-source";
in
{
  systemd.tmpfiles.rules = [
    "d ${stateDir} 0755 root root - -"
  ];

  system.activationScripts.lnbitsbox-funding-source = ''
    mkdir -p ${stateDir}
    chmod 0755 ${stateDir}
    if [ ! -f ${selectedFile} ]; then
      echo spark > ${selectedFile}
      chmod 0644 ${selectedFile}
    fi
  '';
}
