{ pkgs, phoenixd }:

let
  version = "0.7.3";
  java = pkgs.jdk21_headless;
  gradlePackages = pkgs.callPackage "${pkgs.path}/pkgs/development/tools/build-managers/gradle/default.nix" { };
  gradle = (gradlePackages.mkGradle {
    version = "8.9";
    hash = "sha256-1yXXB7+r1N/clYxiQAOzyArMwD9wN7USLEsdDvFc7Ks=";
    defaultJava = java;
  }).wrapped;
in
let
  self = pkgs.stdenv.mkDerivation {
  pname = "phoenixd";
  inherit version;

  src = phoenixd;
  patches = [ ./phoenixd-no-git.patch ];

  nativeBuildInputs = [ gradle pkgs.unzip ];

  # The upstream linux-arm64 native binary is unreliable on NixOS/aarch64.
  # Build the JVM distribution from source instead.
  mitmCache = gradle.fetchDeps {
    pkg = self;
    data = ./phoenixd-deps.json;
  };

  __darwinAllowLocalNetworking = true;
  gradleBuildTask = "jvmDistZip";
  gradleFlags = [ "-Dorg.gradle.java.home=${java}" ];
  PHOENIXD_GIT_COMMIT = "nix";
  PHOENIXD_JVM_ONLY = "1";

  doCheck = false;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/lib $out/bin
    unzip -q build/distributions/phoenixd-${version}-jvm.zip -d $out/lib
    mv $out/lib/phoenixd-${version}-jvm $out/lib/phoenixd

    substituteInPlace $out/lib/phoenixd/bin/phoenixd \
      --replace-fail 'if [ -n "$JAVA_HOME" ] ; then' 'JAVA_HOME="${java}"\nif [ -n "$JAVA_HOME" ] ; then'
    substituteInPlace $out/lib/phoenixd/bin/phoenix-cli \
      --replace-fail 'if [ -n "$JAVA_HOME" ] ; then' 'JAVA_HOME="${java}"\nif [ -n "$JAVA_HOME" ] ; then'

    ln -s $out/lib/phoenixd/bin/phoenixd $out/bin/phoenixd
    ln -s $out/lib/phoenixd/bin/phoenix-cli $out/bin/phoenix-cli

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "Minimal self-custodial Lightning node with an HTTP API";
    homepage = "https://github.com/ACINQ/phoenixd";
    license = licenses.asl20;
    platforms = platforms.linux;
    sourceProvenance = with sourceTypes; [
      fromSource
      binaryBytecode # Gradle MITM cache
    ];
  };
  };
in
self
