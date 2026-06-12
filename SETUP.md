# Argosy Project Setup

Instructions for setting up a working copy of the Argosy project on a
Windows machine with WSL (Windows Subsystem for Linux).


## Prerequisites

- Windows 10/11 with WSL2 enabled (Ubuntu distribution)
- [Miniconda](https://docs.anaconda.com/miniconda/) installed in WSL
- AWS CLI installed in WSL (`sudo apt install awscli` or via pip)
- Git installed in WSL


## 1. Clone the Repository

```bash
cd ~
git clone https://github.com/robfatland/argosy.git
```

If you plan to contribute changes, fork the repo on GitHub first, then clone
your fork and add upstream:

```bash
git clone https://github.com/YOUR_USERNAME/argosy.git ~/argosy
cd ~/argosy
git remote add upstream https://github.com/robfatland/argosy.git
```


## 2. Create the Conda Environment

```bash
cd ~/argosy
conda env create -f environment.yml
conda activate argo-env2
```

This creates the `argo-env2` environment with all pinned dependencies. To
activate it in future sessions:

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate argo-env2
```


## 3. Create the Data Directory Structure

The project expects data in `~/ooi/` (separate from the repo):

```bash
mkdir -p ~/ooi/postproc/pp06
mkdir -p ~/ooi/analysis/sga
mkdir -p ~/ooi/metadata
mkdir -p ~/ooi/visualizations
```


## 4. Download pp06 Data from S3

The pp06 dataset (~15 GB, ~151K NetCDF shard files) is hosted on a public S3
bucket. No AWS credentials needed:

```bash
aws s3 sync s3://s3ooi/pp06/ ~/ooi/postproc/pp06/ --no-sign-request
```

This will take 10-30 minutes depending on network speed.


## 5. Verify the Setup

Start JupyterLab:

```bash
cd ~/argosy
jupyter lab
```

Open a new notebook and run:

```python
%run /home/YOUR_USERNAME/argosy/bundle_chart.py
```

Replace `YOUR_USERNAME` with your WSL username. When prompted:
- Start year: `2023`
- End year: `2023`

The bundle chart widget should appear with sensor dropdowns, sliders, and
navigation buttons. Select source `pp06` from the dropdown.


## 6. Key Directories

| Path | Contents |
|------|----------|
| `~/argosy/` | Code, documentation, notebooks (Git-tracked) |
| `~/argosy/sga/` | Spectral Graph Analysis module scripts |
| `~/ooi/postproc/pp06/` | QC-filtered shard data (from S3) |
| `~/ooi/analysis/sga/` | SGA intermediate outputs |
| `~/ooi/metadata/` | Profile indices, manifests |


## 7. Key Files

| File | Purpose |
|------|---------|
| `ArgosyOverview.md` | Project entry point and documentation index |
| `SpectralGraphAnalysis.md` | SGA module-by-module guide |
| `DevelopmentLog.md` | Progress tracking and next steps |
| `SessionState.md` | Last session state (for AI continuity) |
| `bundle_chart.py` | Interactive bundle plot visualization |
| `sga/sga_config.py` | SGA pipeline configuration |


## 8. Contributing (Pull Request Workflow)

1. Ensure your fork is up to date:
   ```bash
   git fetch upstream
   git checkout master
   git merge upstream/master
   ```

2. Create a branch for your changes:
   ```bash
   git checkout -b my-feature
   ```

3. Make changes, commit, push to your fork:
   ```bash
   git add .
   git commit -m "description of changes"
   git push origin my-feature
   ```

4. Open a Pull Request on GitHub from your branch to `robfatland/argosy:master`.


## 9. Troubleshooting

- **JupyterLab won't start**: Ensure `argo-env2` is activated.
- **Bundle chart widgets don't render**: Run `jupyter labextension list` and
  verify `@jupyter-widgets/jupyterlab-manager` is present. If not:
  `pip install ipywidgets jupyterlab-widgets`
- **S3 sync fails**: Verify AWS CLI is installed (`aws --version`). For public
  buckets, `--no-sign-request` is required.
- **Environment creation fails**: Try `conda env create -f environment.yml --force`
  to clean-create. If specific packages fail, try removing the `prefix:` line
  from `environment.yml`.
