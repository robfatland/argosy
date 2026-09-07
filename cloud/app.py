#!/usr/bin/env python3
"""
CDK app for the argosy Phase 1 pipeline runner — a disposable EC2 instance.

`cdk deploy` = Create button: launches one on-demand EC2 instance with a 1 TB gp3
root volume, an IAM role granting S3 access to the s3ooi bucket + SSM, a security group
with NO inbound rules, and user-data that installs miniconda + clones argosy. Access is
KEYLESS via SSM Session Manager: `aws ssm start-session --target <instance-id>`.

`cdk destroy` = Delete button: tears the whole stack down — instance, volume, role,
security group — so billing stops and nothing lingers (the EBS volume is part of the
stack, so it is deleted with it).

Configuration via CDK context (or env vars); see cloud/README.md:
  - instance_type : default 'c6i.xlarge' (4 vCPU; well under $0.40/hr in us-west-2)
  - bucket        : default 's3ooi'
No SSH key or ssh_cidr — connect via SSM.
"""
import os
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class ArgosyPipelineStack(Stack):
    def __init__(self, scope: Construct, cid: str, **kwargs):
        super().__init__(scope, cid, **kwargs)

        instance_type = self.node.try_get_context("instance_type") or "c6i.xlarge"
        bucket = self.node.try_get_context("bucket") or "s3ooi"

        # Default VPC (no NAT/extra cost); instance goes in a public subnet for outbound
        # access to OOINET/S3. Access is KEYLESS via SSM Session Manager — no SSH.
        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        # Security group: NO inbound rules (no SSH port open). Outbound allowed so the SSM
        # agent can reach the SSM service and the pipeline can reach OOINET/S3.
        sg = ec2.SecurityGroup(self, "ArgosySG", vpc=vpc,
                               description="argosy pipeline runner (SSM, no inbound)",
                               allow_all_outbound=True)

        # IAM role: S3 access to the argosy bucket (+ SSM for keyless console access).
        role = iam.Role(self, "ArgosyRole",
                        assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:DeleteObject"],
            resources=[f"arn:aws:s3:::{bucket}", f"arn:aws:s3:::{bucket}/*"]))

        # 1 TB gp3 ROOT volume; deleted with the instance/stack. Sized for the full oo
        # raw download (~300-400 GB across ~10 years) plus redux shards + pp06 headroom,
        # all processed on-box before syncing to S3 (local-then-sync).
        # IMPORTANT: device_name MUST match the AMI's root device or CDK adds this as a
        # SECOND disk (leaving the tiny 8 GB AMI root in place). Amazon Linux 2023's root
        # device is /dev/xvda (surfaces as nvme0n1). Using that grows the actual root.
        root_volume = ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(
                1000, volume_type=ec2.EbsDeviceVolumeType.GP3, delete_on_termination=True),
        )

        # user-data: install miniconda + git, clone argosy, create env. Does NOT auto-run
        # the pipeline (you SSH in, populate download_link_list.txt, then run run_pipeline.sh).
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "set -x",
            "dnf install -y git wget || yum install -y git wget",
            "cd /home/ec2-user",
            "wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O mc.sh",
            "bash mc.sh -b -p /home/ec2-user/miniconda3",
            "git clone https://github.com/robfatland/argosy.git /home/ec2-user/argosy || true",
            "chown -R ec2-user:ec2-user /home/ec2-user",
            # Create the MINIMAL pipeline env (not environment.yml). The full analysis env
            # pulls ~2 GB of CUDA/MKL/Jupyter this box never uses; the pipeline only needs
            # the packages below. Accept conda channel ToS first, else create fails
            # non-interactively (CondaToSNonInteractiveError).
            "sudo -u ec2-user bash -lc 'source ~/miniconda3/etc/profile.d/conda.sh; "
            "conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main; "
            "conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r; "
            "conda create -y -n argosy python=3.11 xarray netcdf4 pandas numpy scipy requests beautifulsoup4 boto3 awscli'",
        )

        instance = ec2.Instance(
            self, "ArgosyRunner",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=sg,
            role=role,
            block_devices=[root_volume],
            user_data=user_data,
        )

        cdk.CfnOutput(self, "InstanceId", value=instance.instance_id)
        cdk.CfnOutput(self, "Connect",
                      value=f"aws ssm start-session --target {instance.instance_id}")


app = cdk.App()
ArgosyPipelineStack(
    app, "ArgosyPipelineStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-west-2"),
    ),
)
app.synth()
