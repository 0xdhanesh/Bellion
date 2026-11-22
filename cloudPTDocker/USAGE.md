# cloudPTDocker: command-line usage

Cloud configuration assessment. Maintainer: **0xdhanesh** <dhanesh.professional@gmail.com>.
For agent clients, see [MCPUSAGE.md](MCPUSAGE.md); for image limitations, see [README.md](README.md).

## 1. Build on the host

Commands in this section run in a Bash/Zsh terminal on your **host**, from the
repository root. Docker must be installed and its daemon running. Replace input
filenames, device IDs, and example domains with your own artifacts and authorized
lab targets. Network examples perform real requests when run.

```bash
docker info
mkdir -p cloudPTDocker/workspace
docker build -f cloudPTDocker/Dockerfile -t cloudptdocker:latest .
# Put input files in cloudPTDocker/workspace before opening the shell.
```

The build context is the repository root (`.`), because `shared/` is required.
Builds download dependencies. Image tags are lowercase.

## 2. Spawn a shell or execute one command

On the host, from the repository root:

```bash
# Interactive Bash shell; the mounted folder becomes /workspace.
docker run --rm -it --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/cloudPTDocker/workspace,dst=/workspace" \
  cloudptdocker:latest

# Alternative: /bin/sh instead of Bash.
docker run --rm -it --entrypoint=/bin/sh \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/cloudPTDocker/workspace,dst=/workspace" \
  cloudptdocker:latest

# One command, without a TTY or a persistent shell.
docker run --rm --cap-drop=ALL --security-opt=no-new-privileges \
  --ulimit fsize=16777216:16777216 \
  --mount "type=bind,src=$PWD/cloudPTDocker/workspace,dst=/workspace" \
  cloudptdocker:latest python3 -c 'print("container ready")'

# Compose alternative; uses the same workspace directory.
docker compose -f cloudPTDocker/compose.yaml run --build --rm tools
```

Inside the shell, `whoami` prints `0xdhanesh`, `pwd` prints `/workspace`, and
`ls -la /workspace` shows the mounted inputs. `exit` closes and removes the
container. Files under `/workspace` remain in `cloudPTDocker/workspace` on the host;
files elsewhere disappear unless separately mounted. To work from any host
folder, use the helpers in the [shell helpers guide](../docs/SHELL_HELPERS.md).

The user is UID 10001, without sudo. On native Linux, either grant this UID
workspace access or add `--user "$(id -u):$(id -g)" -e HOME=/tmp` before the image
in `docker run`. For offline artifact work, add `--network=none` there as well.
Compose overrides must supply equivalent settings. For a foreign architecture,
use matching `--platform linux/amd64` build/run options; emulated execution and
ptrace are not guaranteed. The supplied launches cap individual files at 16 MiB;
raise the `--ulimit fsize=SOFT:HARD` values deliberately for larger reports.

## 3. Execute the installed commands

Run these examples **inside the container** with your own input files and
explicitly authorized targets. Each executable in tools.json is covered below.
Use its help for all options. Report files under `/workspace` persist on the host.

| Executable | Example | Expected output |
| --- | --- | --- |
| `aws` | `aws sts get-caller-identity --output json` | AWS account, principal ARN and user ID for the configured identity. |
| `az` | `az account show --output json` | Current Azure tenant/subscription metadata after authentication. |
| `gcloud` | `gcloud projects list --format=json` | Google Cloud projects visible to the authenticated identity. |
| `openssl` | `openssl x509 -in /workspace/certificate.pem -text -noout` | Certificate properties; does not establish a trusted chain. |
| `curl` | `curl -I --max-time 15 https://LAB_HOST` | Response headers from an authorized lab endpoint. |
| `jq` | `jq '.Account' /workspace/identity.json` | A field selected from a saved CLI JSON report. |
| `python3` | `python3 -c 'import boto3; print(boto3.__version__)'` | Installed AWS SDK version; no cloud API call. |

### Authenticate only to the intended cloud account

AWS CLI **v1**, Azure CLI and Google Cloud CLI are pinned in
[versions.json](versions.json). AWS and Azure
CLIs have isolated Python environments to avoid changing the MCP bridge's
libraries. Google Cloud's archive SHA-256 values are recorded in
[gcloud-release.json](gcloud-release.json).

For AWS, prefer the engagement's existing short-lived credential workflow.
Forward variables explicitly from the host by adding these flags before the
image in the shell or MCP Docker arguments:

```bash
-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -e AWS_DEFAULT_REGION
```

This is a Docker argument fragment, not a standalone command. The variables
must exist in the environment of the process launching Docker. Do not paste
secrets into a prompt or commit them. Alternatively mount a deliberately
prepared credentials/config directory at `/home/0xdhanesh/.aws` read-only and
set `AWS_PROFILE` to the intended profile. This image does not provide AWS CLI
v2 SSO login commands; mount credentials usable by CLI v1 or use short-lived
environment credentials.

For Azure, in the interactive container shell:

```bash
az login --use-device-code
az account show --output json
az resource list --subscription SUBSCRIPTION_ID --output json > /workspace/azure-resources.json
```

Mount a dedicated host directory at `/home/0xdhanesh/.azure` if authentication
state must persist or be reused by MCP. It must be writable by UID 10001.
For a scoped noninteractive service-principal workflow, configure the approved
identity using the provider's supported authentication mechanism outside an
MCP password prompt; do not expose credentials in the conversation.

For Google Cloud, in the interactive container shell:

```bash
gcloud auth login --no-launch-browser
gcloud projects list --format=json
gcloud compute instances list --project PROJECT_ID --format=json > /workspace/gcp-instances.json
```

Persist a dedicated `/home/0xdhanesh/.config/gcloud` directory to reuse that
identity. Alternatively mount an approved service-account key file and use
`gcloud auth activate-service-account --key-file=/workspace/service-account.json`
only when that is the authorized credential workflow. Setting
`GOOGLE_APPLICATION_CREDENTIALS` alone does not log the gcloud CLI in; ADC and
CLI account authentication are distinct. No credentials are built into images.

For AWS identity and a bounded region-specific inventory:

```bash
aws sts get-caller-identity --output json
aws ec2 describe-instances --region REGION --output json > /workspace/aws-instances.json
```

Identity/inventory calls need network access and permissions. Limit subscription,
project, account, and region explicitly. Access-denied and partial listings are
expected outcomes to report. The container does not grant permissions, bypass
MFA, emulate a cloud provider, or include Kubernetes/VPN tooling. Avoid resource
creation or modification when the engagement calls for read-only assessment.

Sources: [AWS CLI](https://github.com/aws/aws-cli),
[Azure CLI](https://github.com/Azure/azure-cli),
[Google Cloud installation](https://docs.cloud.google.com/sdk/docs/install-sdk).



## 4. Preserve results and verify the environment

Shell redirection works inside the shell. For example:

```bash
mkdir -p /workspace/results
python3 -c 'print("analysis notes")' > /workspace/results/notes.txt
cat /workspace/results/notes.txt
exit
```

Back on the host, from the repository root:

```bash
ls -la cloudPTDocker/workspace/results
./scripts/verify.sh cloudPTDocker
```

The verification script checks the image build, installed tools, account, and
real stdio MCP interactions using local fixtures. It does not validate your
specific target, physical device, or optional analysis providers.

| Problem | Check |
| --- | --- |
| Cannot connect to Docker | Start Docker Desktop/Engine and run `docker info` on the host. |
| Image missing | Build from the repository root using the exact lowercase tag above. |
| Input file missing | Check the host bind path and use `/workspace/...` inside the container. |
| Permission denied writing reports | Check workspace ownership/UID mapping on native Linux. |
| File size limit exceeded | Adjust the supplied fsize limit for the intended artifact/report size. |
| Network lookup or connection fails | Check offline mode, lab reachability, DNS, and service settings. |
| Tool reports missing engine/device | Follow [README.md](README.md); installing a CLI does not supply an external provider or device. |
