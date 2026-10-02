{ pkgs, lnbits }:

let
  lib = pkgs.lib;
  python = pkgs.python312;
  pyproject-nix = lnbits.inputs.pyproject-nix;
  uv2nix = lnbits.inputs.uv2nix;
  build-system-pkgs = lnbits.inputs.build-system-pkgs;
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = lnbits; };
  uvLockedOverlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
  plus = a: b: lib.unique ((if a == null then [] else a) ++ b);
  wasmtimeWheel = pkgs.fetchurl {
    url = "https://files.pythonhosted.org/packages/1c/c3/a957b226979daaeb09ec024562e9aac05e475a954537e6f150eb60bca84d/wasmtime-48.0.0-py3-none-manylinux2014_aarch64.whl";
    hash = "sha256-JvzjYT/vvimijp1lncozJugAWThY5XWMrQhuuAKzt2Y=";
  };
  overrides = final: prev: {
    embit = prev.embit.overrideAttrs (old: {
      nativeBuildInputs = plus (old.nativeBuildInputs or []) [ prev.setuptools ];
    });
    "http-ece" = prev."http-ece".overrideAttrs (old: {
      nativeBuildInputs = plus (old.nativeBuildInputs or []) [ prev.setuptools ];
    });
    pyqrcode = prev.pyqrcode.overrideAttrs (old: {
      nativeBuildInputs = plus (old.nativeBuildInputs or []) [ prev.setuptools ];
    });
    tlv8 = prev.tlv8.overrideAttrs (old: {
      nativeBuildInputs = plus (old.nativeBuildInputs or []) [ prev.setuptools ];
    });
    secp256k1 = prev.secp256k1.overrideAttrs (old: {
      nativeBuildInputs = plus (old.nativeBuildInputs or []) [ prev.setuptools pkgs.pkg-config prev.cffi prev.pycparser ];
      buildInputs = plus (old.buildInputs or []) [ pkgs.secp256k1 ];
      propagatedBuildInputs = plus (old.propagatedBuildInputs or []) [ prev.cffi prev.pycparser ];
      env = (old.env or {}) // { PKG_CONFIG = "${pkgs.pkg-config}/bin/pkg-config"; };
    });
    pynostr = prev.pynostr.overrideAttrs (old: {
      nativeBuildInputs = plus (old.nativeBuildInputs or []) [ prev.setuptools-scm ];
    });
    wasmtime = prev.wasmtime.overrideAttrs (_old: { src = wasmtimeWheel; });
  };
  pythonSet = (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope
    (lib.composeManyExtensions [
      build-system-pkgs.overlays.default
      uvLockedOverlay
      overrides
    ]);
in
pythonSet.mkVirtualEnv "lnbits-env" workspace.deps.default
