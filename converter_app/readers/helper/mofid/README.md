# MOF metadata for CIF files

The CIF reader can enrich every `.cif` file with the seven MOFid identifiers,
stored on the first meta table as `mofid.<key>`:

```
mofid.mofid            [Cu][Cu].[O-]C(=O)c1cc(...)  MOFid-v1.tbo.cat0.NO_REF;755080
mofid.mofkey           Cu.QMKYBPDZANOJGF.MOFkey-v1.tbo.NO_REF
mofid.smiles           [Cu][Cu].[O-]C(=O)c1cc(...)
mofid.smiles_nodes     [Cu][Cu]
mofid.smiles_linkers   [O-]C(=O)c1cc(cc(c1)C(=O)[O-])C(=O)[O-]
mofid.topology         tbo
mofid.cat              0
```

Lists are joined with `.`, missing values become empty strings, so every value
is a string as the reader base class expects.

The work is done by the [snurr-group `mofid`](https://github.com/snurr-group/mofid)
pipeline, which is *not* pure Python: it drives a compiled C++ decomposer (`sbu`)
and a Java topology matcher (Systre). That is why it is optional and why there
are three ways to reach it.

## The three tiers

`converter_app/readers/helper/mofid_client.py` picks the first one that is
configured:

| Tier | Trigger | How it runs |
| --- | --- | --- |
| 1 · service | `MOFID_SERVICE_URL` is set | HTTP POST to `<url>/analyze` |
| 2 · native | `MOFID_HOME` is set, or `mofid` is importable | subprocess on this host |
| 3 · off | neither | no MOF metadata; reader behaves as before |

Tier 3 is the default: without configuration nothing changes.

### Tier 1 — service (recommended)

Inside the ELN, `mof_service` already runs as its own container. No
Docker-in-Docker is involved: the converter and the service are siblings on the
`chemotion` network, so the converter only needs the URL.

```yaml
  converter:
    image: ${IMG_CONVERTER}
    environment:
      - MOFID_SERVICE_URL=http://mof_service:5000/
    networks: [chemotion]
```

Standalone, use the image in this directory (port **5006**, so it does not clash
with the ELN's service on 5000):

```bash
cd converter_app/readers/helper/mofid
docker build -t chemconverter-mofid:latest .
docker run -d --name mofid -p 5006:5006 --restart unless-stopped chemconverter-mofid:latest

curl -s http://localhost:5006/health          # {"status":"ok"}
export MOFID_SERVICE_URL=http://localhost:5006/
```

The build takes ~20 minutes; build it once in CI and pull the image instead if
you deploy this more than once. The endpoint is API-compatible with the ELN's
`mof_service`, so `MOFID_SERVICE_URL` can point at either — this one just returns
the seven keys and nothing else.

Do **not** wire the converter up to build or start containers on its own. It
would need Docker socket access, and a 20-minute build triggered by a file upload
cannot fit inside a request. Run the two commands above once, deliberately.

### Tier 2 — native subprocess (no Docker)

```bash
sudo ./install_mofid.sh                 # builds into /opt/mofid, ~20 min, ~500 MB
export MOFID_HOME=/opt/mofid
```

The script checks the prerequisites (git, make, a C++ compiler, cmake, a JRE),
pins the same upstream commit as the Dockerfile, and finishes with a self-test
against a reference structure. Linux and macOS only — the mofid Makefile does not
build natively on Windows.

Two things to know:

* **The build is not relocatable.** `RUNPATH` and `mofid/Python/paths.py` hold
  absolute paths. Copying `/opt/mofid` to another machine or another directory
  breaks it. Rerun the script there instead.
* **A broken install fails silently.** When `sbu` cannot start, mofid swallows
  the error and returns the same `no_mof`/`NA` result a genuine non-MOF CIF
  produces. Both the install script's self-test and the client's stderr check
  exist to catch that; run `./install_mofid.sh --force` if the self-test fails.

The client runs the pipeline as a subprocess rather than importing it. mofid sets
`BABEL_DATADIR` at import time, and it reads the `commit_ref` that ends up inside
the MOFid/MOFkey from `.git/ORIG_HEAD` relative to the working directory — run
in-process from a git checkout, the converter's own commit hash would land in
every identifier. A subprocess with a pinned cwd avoids both and allows a hard
timeout.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `MOFID_SERVICE_URL` | — | Tier 1 endpoint, e.g. `http://localhost:5006/` |
| `MOFID_HOME` | — | Tier 2 installation directory |
| `MOFID_PYTHONPATH` | `$MOFID_HOME/pythonpath` | override for a `pip install`ed mofid |
| `MOFID_TIMEOUT` | `180` | seconds per CIF |
| `MOFID_ENABLED` | `true` | set to `false` to force tier 3 |

## Reproducibility

The pipeline version influences the identifiers, so the Dockerfile and the
install script pin the same upstream commit (`MOFID_REF`). Keep it in sync with
the ELN's `mof_service` if you want the converter's MOFkeys to match the ones
stored in the ELN. Bump it deliberately, not by tracking a branch.

## Cost per file

A MOF takes a few seconds (4 s for a Cu-BTC framework); a non-MOF CIF is
rejected in about 0.2 s. Worst case is bounded by Systre's own 30 s timeout,
twice, plus the decomposition — hence the 180 s client default.
