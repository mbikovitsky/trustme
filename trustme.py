#!/usr/bin/env python3


import logging
import argparse
import json
import uuid
import tempfile
import os
import subprocess
import hashlib
import shutil


LOG_LEVEL = logging.INFO


def main():
    # Configure logging
    logging.basicConfig(level=LOG_LEVEL)

    # Configure argument parsing
    parser = argparse.ArgumentParser(
        description="Re-signs VSIXs in the VS 2015 offline installer"
    )
    parser.add_argument("config", help="Path to the configuration file")
    parser.add_argument("pfx",
                        help="Path where the generated PFX will be stored")

    # Parse arguments
    namespace = parser.parse_args()

    # Load the configuration
    logging.info("Reading configuration from %s", namespace.config)
    with open(namespace.config, mode="r") as f:
        configuration = json.load(f)

    # Read the configuration
    tools = configuration["tools"]
    packages = configuration["packages"]

    # Generate a certificate for re-signing the VSIXs
    pfx_path = generate_certificate(tools["makecert"], tools["pvk2pfx"])

    # Re-sign every single package
    try:
        for package in packages:
            sign_package(tools["vsixsigntool"], pfx_path, package)
    except:
        force_delete(pfx_path)
        raise

    # Copy PFX to where the user indicated
    logging.info("Moving PFX from %s to %s...",
                 pfx_path,
                 namespace.pfx)
    shutil.move(pfx_path, namespace.pfx)


def generate_certificate(makecert, pvk2pfx):
    logging.info("Generating certificate")

    unique_name = str(uuid.uuid4())
    temp_dir = tempfile.gettempdir()
    cert_path = os.path.join(temp_dir, unique_name + ".cer")
    pvk_path = os.path.join(temp_dir, unique_name + ".pvk")
    pfx_path = os.path.join(temp_dir, unique_name + ".pfx")

    try:
        makecert_cmd = [makecert,
                        "-r",
                        "-pe",
                        "-n", "CN=Microsoft Corporation",
                        "-a", "sha256",
                        "-cy", "authority",
                        "-sky", "signature",
                        "-len", "4096",
                        "-sv", pvk_path,
                        cert_path]
        logging.info("Launching makecert with %s", makecert_cmd)
        subprocess.check_call(makecert_cmd, stdout=subprocess.DEVNULL)

        pvk2pfx_cmd = [pvk2pfx,
                       "-pvk", pvk_path,
                       "-spc", cert_path,
                       "-pfx", pfx_path]
        logging.info("Launching pvk2pfx with %s", pvk2pfx_cmd)
        subprocess.check_call(pvk2pfx_cmd, stdout=subprocess.DEVNULL)
    except:
        force_delete(pfx_path)
    finally:
        force_delete(pvk_path)
        force_delete(cert_path)

    return pfx_path


def sign_package(vsixsigntool, pfx_path, package):
    logging.info("Parsing package: %s", package["name"])

    original_hash = calculate_file_hash(package["vsix"])
    logging.info("Original SHA256: %s", original_hash)

    vsixsigntool_cmd = [vsixsigntool,
                        "sign",
                        "/f", pfx_path,
                        package["vsix"]]
    logging.info("Launching vsixsigntool with %s", vsixsigntool_cmd)
    subprocess.check_call(vsixsigntool_cmd, stdout=subprocess.DEVNULL)

    new_hash = calculate_file_hash(package["vsix"])
    logging.info("New SHA256: %s", new_hash)

    # Read the cache file
    logging.info("Reading cache file...")
    with open(package["cache"], mode="rb") as f:
        cache = f.read()

    logging.info("Patching cache...")
    patched_cache = cache.replace(original_hash.encode("UTF-8"),
                                  new_hash.encode("UTF-8"))

    if patched_cache == cache:
        raise RuntimeError("Cache patching failed!")

    logging.info("Writing patched cache back...")
    with open(package["cache"], mode="wb") as f:
        f.write(patched_cache)


def force_delete(file_path):
    try:
        os.remove(file_path)
    except OSError:
        pass


def calculate_file_hash(path):
    sha256 = hashlib.sha256()

    with open(path, mode="rb") as f:
        sha256.update(f.read())

    return sha256.hexdigest().upper()


if __name__ == "__main__":
    main()
