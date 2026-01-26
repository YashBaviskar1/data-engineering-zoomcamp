

# Docker + Data Pipeline Debugging Notes

## Conceptual Gaps, Failures, and Correct Mental Models

---

## 1. Build Context ≠ Dockerfile Location

### Initial (incorrect) mental model

> “Docker looks for files relative to the Dockerfile location.”

---

### What actually happened

Command executed:

```bash
cd week1/pipeline
docker build -t taxi_data_ingest:v1 .
```

Docker attempted:

```dockerfile
COPY ./pyproject.toml ./python-version ./uv.lock ./
```

Failure:

```text
"/pyproject.toml": not found
```

---

### Why this failed

* The **build context** was `week1/pipeline`
* `pyproject.toml` exists in `week1/`
* Docker **cannot access parent directories**

Docker does **not** infer the build context from the Dockerfile’s location.

---

### Correct mental model

> The **last argument to `docker build` defines the complete file universe available during build time**.

* `.` → build context
* `-f` → specifies only which Dockerfile to use

Docker is **sandboxed at build time**.

---

### Correct practice

If required files exist in `week1/`:

```bash
docker build -f Dockerfile.pipeline -t taxi_data_ingest:v1 .
```

All `COPY` paths must be relative to `week1/`.

---

## 2. Container Filesystem ≠ Host Filesystem

### Initial (incorrect) mental model

> “Passing an absolute path allows the container to read that file.”

Argument passed:

```bash
--database=/home/yashbaviskar/Desktop/.../taxi_zone_lookup.csv
```

Error:

```text
FileNotFoundError: No such file or directory
```

---

### Why this failed

Inside the container:

* `/home/yashbaviskar/...` does not exist
* Containers start with a **clean, isolated filesystem**
* Host files are invisible by default

Absolute paths are **host-relative**, not container-relative.

---

### Correct mental model

> A container is a **separate Linux filesystem** with no awareness of host files unless explicitly mounted.

---

### Correct practice

Mount host directories explicitly:

```bash
docker run -v $(pwd):/data ...
```

Reference **container paths** instead:

```bash
--database=/data/taxi_zone_lookup.csv
```

---

## 3. ENTRYPOINT + CLI Arguments Work Only for Logic, Not Files

### Initial misunderstanding

> “If the script accepts CLI arguments, Docker will handle file access.”

Observed behavior:

* CLI parsing succeeded
* Function execution occurred
* `pandas.read_csv()` failed

---

### Correct mental model

> CLI arguments are **plain strings**.
> File access still follows container filesystem boundaries.

Docker does not automatically map file paths.

---

## 4. `localhost` Inside a Container ≠ Host Machine

### Initial (implicit) assumption

> “If Postgres runs on localhost, `localhost` should work.”

Argument used inside container:

```bash
--pg-host=localhost
```

---

### Why this failed

Inside a container:

* `localhost` refers to the **container itself**
* The host OS is a separate network namespace

---

### Correct mental model

> `localhost` always refers to **the current network namespace**.

* Host `localhost` ≠ container `localhost`

---

## 5. `host.docker.internal` Is Not Portable (Linux-Specific Failure)

### Attempted solution

```bash
--pg-host=host.docker.internal
```

Error:

```text
could not translate host name "host.docker.internal"
Name or service not known
```

---

### Why this failed

* `host.docker.internal` is a **Docker Desktop convenience alias**
* Guaranteed on **Mac and Windows**
* **Not guaranteed on native Linux**

On Linux, this hostname may:

* not exist
* not resolve via DNS
* depend on Docker daemon configuration

---

### Correct mental model

> `host.docker.internal` is a **non-standard convenience**, not a portable networking primitive.

---

## 6. Docker Bridge Networking on Linux (Working Solution)

### Observation

From `ip addr`:

```text
docker0 inet 172.17.0.1
```

---

### Correct mental model

> On Linux, containers communicate with the host via the **docker0 bridge**.

* Containers: `172.17.0.0/16`
* Host gateway: `172.17.0.1`

---

### Correct practice

```bash
--pg-host=172.17.0.1
```

This works because:

* Postgres is bound to the host
* Docker bridge routes traffic correctly

---

## 7. Why This Solution Is Still Not Ideal

Using raw IP addresses:

* works
* but is brittle
* not portable
* not production-grade

---

### Better long-term mental model

> Containers should communicate with **other containers via service names**, not host IPs.

This implies:

* Database runs in a container
* Shared Docker network
* DNS-based service discovery

Example:

```bash
--pg-host=postgres
```

---

## Summary: Corrected Mental Models (Condensed)

### Build Time

* Docker sees **only the build context**
* Dockerfile name and location are irrelevant

### Runtime Filesystem

* Containers cannot see host files by default
* Use explicit volume mounts (`-v`)

### Paths

* Always reason in **container paths**
* Absolute host paths are meaningless inside containers

### Networking

* `localhost` = current container
* `host.docker.internal` is not portable
* Linux host access = `docker0` → `172.17.0.1`

### Professional Takeaway

> All observed Docker failures stemmed from **boundary violations**:
>
> * filesystem boundaries
> * network namespace boundaries
> * build context boundaries

Once these boundaries are respected, Docker behavior becomes predictable.

