This folder `~/argosy/cloud/` contains files for the **Create/Destroy EC2 pipeline runner** —
a disposable on-demand EC2 instance that runs the Phase 1 pipeline (`pipeline/run_pipeline.sh`)
and syncs results to S3, then is torn down. Infrastructure is defined with AWS CDK (Python).

- `app.py` — the CDK app + `ArgosyPipelineStack`: EC2 instance (1 TB gp3 root, deleted with
  the stack), IAM role (S3 access to `s3ooi` + SSM), security group (no inbound; SSM access), and
  user-data that installs miniconda, clones argosy, and creates the `argosy` conda env.
- `cdk.json` — CDK app config. `requirements.txt` — CDK Python deps.

## One-time prerequisites (on this localhost)

- Node.js + the CDK CLI: `npm install -g aws-cdk` (check `cdk --version`).
- **CDK Python libs live in a SEPARATE conda env `argosy-cdk`** (NOT the `argosy` analysis env —
  aws-cdk-lib's deps downgrade typeguard and conflict with the Jupyter Book/Sphinx stack). Create once:
  `conda create -n argosy-cdk python=3.11 -y && conda activate argosy-cdk && pip install aws-cdk-lib constructs`.
  Activate `argosy-cdk` before any `cdk` command.
- AWS credentials configured (`aws configure` / SSO) with permission to create EC2/IAM/EBS.
- Bootstrap the account/region ONCE: `cdk bootstrap aws://<account>/<region>`.
- The Session Manager plugin for the AWS CLI (for keyless connect), one-time on this localhost:
  ```bash
  cd /tmp
  curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o session-manager-plugin.deb
  sudo dpkg -i session-manager-plugin.deb   # if it complains: sudo apt-get install -f
  session-manager-plugin --version          # verify
  ```
  No EC2 key pair is needed — access is via SSM (see below).

## Connecting to the instance: SSM Session Manager (keyless, no open SSH)

This stack uses **AWS Systems Manager (SSM) Session Manager** for shell access instead of
SSH. How it works: the instance runs the SSM agent (built into Amazon Linux 2023) and is
granted the `AmazonSSMManagedInstanceCore` IAM role, which lets it register with the SSM
service and open an *outbound* connection to it. When you run `aws ssm start-session`, your
terminal and the instance meet through the SSM service; AWS brokers an encrypted channel
between them.

Why this is more secure than SSH:
- **No inbound ports.** The security group opens nothing to the internet — no port 22, no
  public SSH surface to scan or brute-force. The instance reaches *out* to SSM; nothing
  reaches *in*. (The stack keeps the instance in a public subnet only for outbound internet
  to OOINET/S3; no ingress rule is required.)
- **No SSH keys to manage or leak.** There is no `.pem` file to store, rotate, or lose.
  Authentication and authorization ride on your existing AWS IAM identity — the same
  credentials you already use for `aws` — so access is governed by IAM policy and logged.
- **Auditable.** Session activity is attributable to your IAM principal and can be logged to
  CloudTrail/CloudWatch, unlike anonymous SSH.

Connect with:
```bash
aws ssm start-session --target <instance-id>
```
(The instance id is a stack output from `cdk deploy`.) Once in, `sudo su - ec2-user` to become
the pipeline user, then run `pipeline/run_pipeline.sh`.

## Create (deploy)

```bash
conda activate argosy-cdk
cd ~/argosy/cloud
cdk deploy \
  -c instance_type=c6i.xlarge        # optional; default c6i.xlarge (~<$0.40/hr in us-west-2)
```
No key pair or `ssh_cidr` needed — access is keyless via SSM. Outputs the instance id (used to
start a session). The user-data bootstrap (miniconda + clone + env) runs on first boot; give it
a few minutes.

## Run the pipeline (via SSM Session Manager)

```bash
aws ssm start-session --target <instance-id>   # instance-id from the deploy output
sudo su - ec2-user
# populate the OOINET staging URLs:
nano ~/argosy/download_link_list.txt
# run one site end-to-end (download -> shard -> pp -> sync to S3):
bash ~/argosy/pipeline/run_pipeline.sh oo
```
`run_pipeline.sh` uses `ARGOSY_SITE` so all steps target the chosen site. Results sync to
`s3://s3ooi/<site>/{redux,postproc,metadata}/`.

## Destroy (delete — stops billing)

```bash
cd ~/argosy/cloud
cdk destroy
```
This deletes the instance, the 1 TB volume, the role, and the security group. **Verify** in
the EC2 console that no instance/volume lingers (orphaned EBS is the usual way to keep paying).

## Cost note

On-demand `c6i.xlarge` is roughly $0.17/hr in us-west-2 (well under the $0.40/hr ceiling);
1 TB gp3 is ~$0.08/GB-month but prorated to the hours the stack exists and deleted on destroy
(a multi-hour run's storage cost is a couple dollars). A one-site processing run is a few
dollars total. No NAT gateway (public subnet, default VPC) to avoid standing cost.

## Known gaps (see pipeline/run_pipeline.sh + DevelopmentLog)

- Sharding is still in `chapters/DataSharding.ipynb`; `run_pipeline.sh` skips it with a notice
  until it is extracted to `pipeline/shard.py` (or run headless via nbconvert).
- Spot instances / AWS Batch are a future optimization; this first pass is a plain on-demand box.
