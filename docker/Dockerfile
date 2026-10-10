# simcore runtime: pinned OpenModelica + the Python packages our library needs.
# Built automatically by `docker compose build` (see docker-compose.yml).
FROM openmodelica/openmodelica:v1.27.1-ompython

# Newer Debian/Ubuntu images block system-wide pip installs by default (PEP 668).
# Inside a single-purpose container that protection isn't needed, so we allow it.
ENV PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_NO_CACHE_DIR=1

# Make sure pip exists (some base images ship Python without it).
RUN (python3 -m pip --version || (apt-get update \
     && apt-get install -y --no-install-recommends python3-pip \
     && rm -rf /var/lib/apt/lists/*))

# Pinned versions: change deliberately, like the OpenModelica tag above.
#   pandas  - read and filter simulation results (CSV)
#   plotly  - interactive charts (zoom, hover) saved as HTML
#   pytest  - automated tests
RUN python3 -m pip install "pandas==2.2.3" "plotly==5.24.1" "pytest==8.3.4"
