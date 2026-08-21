# Tier 1 of the converter's MOF support: the snurr-group `mofid` pipeline behind
# a small Flask app on port 5006, so the CIF reader can POST a CIF and get the
# MOFid/MOFkey back over HTTP.
#
# Build and run (from this directory):
#   docker build -t chemconverter-mofid:latest .
#   docker run -d --name mofid -p 5006:5006 chemconverter-mofid:latest
# then point the converter at it:
#   MOFID_SERVICE_URL=http://localhost:5006/
FROM continuumio/miniconda3:24.5.0-0

# Toolchain for building mofid, which compiles its own bundled OpenBabel from
# source. Two deliberate version pins:
#   * cmake<4  -- that submodule declares cmake_minimum_required below 3.5, which
#     CMake 4.x refuses outright. CMAKE_POLICY_VERSION_MINIMUM is belt-and-braces.
#   * gcc/gxx 13 -- OpenBabel vendors RapidJSON 1.1.0, a hard compile error on
#     GCC 14 but fine on 13, and conda-forge's cxx-compiler now defaults to 14.
#
# Note there is no `openbabel` conda package here, unlike the ELN's mof_service:
# the Python bindings are only needed for the component ratios that service adds
# on top. The seven identifiers below come from the compiled C++ helpers alone.
RUN conda install -y -c conda-forge \
        python=3.11 \
        openjdk \
        "cmake<4" \
        make \
        "gcc=13" \
        "gxx=13" \
    && conda clean -afy

ENV CMAKE_POLICY_VERSION_MINIMUM=3.5
# The mofid Makefile honours CC/CXX; point them at the pinned toolchain.
ENV CC=gcc CXX=g++

# Pin a specific upstream commit for reproducible identifiers -- the pipeline
# version influences the resulting MOFid, so bump this deliberately (and re-test
# the toolchain pins above) rather than tracking a moving branch. This is the
# same commit the ELN's mof_service pins, so both produce identical results.
# A SHA rather than a ref name is why this is init+fetch and not clone --branch.
ARG MOFID_REF=36873683083c7bc62c1da2062df2833adc35b48a
RUN git init /opt/mofid \
    && git -C /opt/mofid fetch --depth 1 https://github.com/snurr-group/mofid.git ${MOFID_REF} \
    && git -C /opt/mofid checkout --detach FETCH_HEAD

# `make init` compiles the C++ helpers; set_paths.py bakes their absolute paths
# into the package, so it has to run before `pip install .`.
WORKDIR /opt/mofid
RUN make init \
    && python set_paths.py \
    && pip install .

# Fail the build rather than ship an image whose pipeline silently reports
# 'not a MOF' for every input: a working install identifies this reference
# structure as the tbo net.
RUN python -c "\
from mofid.run_mofid import cif2mofid; \
r = cif2mofid('/opt/mofid/Resources/TestCIFs/P1-Cu-BTC.cif', output_path='/tmp/selftest'); \
assert r['topology'] == 'tbo', r; \
print('mofid self-test OK:', r['mofkey'])"

WORKDIR /opt/app
RUN pip install --no-cache-dir flask==3.0.3 gunicorn==22.0.0
COPY service.py .

EXPOSE 5006

# Systre can take a while on large frameworks and requests are low-volume. The
# worker timeout stays above the client's (MOFID_TIMEOUT, 180s by default) so the
# client gives up first with a clean error instead of racing gunicorn's kill.
CMD ["gunicorn", "--bind", "0.0.0.0:5006", "--workers", "2", "--timeout", "300", "service:app"]
