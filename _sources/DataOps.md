# DataOps

Operational procedures for managing the `~/ooi` data filesystem: cloud backup to
S3 and localhost disk-space management. These are distinct from the data-transformation
logic in `PostProcessing.md` (which covers redux → ppNN); this file covers the
infrastructure that keeps the data available and the local disk from filling up.

See `PostProcessing.md` for the postprocessing pipeline and `ArgosyOverview.md` for
the full document index.


## S3 bucket layout (`s3ooi`)

The bucket mirrors the per-site local layout (restructured Aug 2026):

```
s3://s3ooi/
  <site>/redux/<yyyy>/...           e.g. sb/redux/2022/
  <site>/postproc/<pp>/<yyyy>/...   e.g. sb/postproc/pp06/2022/
  ooinet/rca/...                    raw archive (legacy keys, see note)
```

- Public-read policy grants unauthenticated `s3:GetObject` on `sb/redux/*` and
  `sb/postproc/*` (and `ListBucket` on those prefixes). Metadata/analysis and
  `ooinet/` remain private. To add a site, extend the policy with `<site>/redux/*`
  and `<site>/postproc/*` deliberately.
- **`ooinet/` exception:** the 204 GB raw archive was NOT re-keyed during the
  per-site restructure — it retains its original `ooinet/rca/...` scheme. Re-keying
  204 GB for tidiness isn't worth the cost/time; revisit only when a second site's
  raw data is added.


## S3 sync: data to AWS object storage


Data from `ooinet` is voluminous so we start with the idea of writing it to object storage on AWS using the S3 "bucket" service. The same idea applies to other stages of data preparation, particularly "analysis-ready" post-processing datasets such as `pp06`. This section describes stored data, synch commands from localhost to S3; double checking everything is ok; and access/download commands.


The `~/ooi/<site>/ooinet/` directory (raw source NetCDF from OOINET) is backed up
to S3. This allows the local copy to be deleted to free disk space, with the data
retrievable from the cloud if re-sharding is ever needed.

### Sync command

```bash
aws s3 sync ~/ooi/sb/ooinet/ s3://s3ooi/ooinet/ --storage-class STANDARD_IA
```

- Uploads only new/changed files (compares size and modification time)
- `STANDARD_IA`: ~$0.0125/GB/month (~$2.55/month for 204 GB)
- One-directional: local → S3. Does not delete from S3 if deleted locally.
- Safe to interrupt with Ctrl+C and restart — picks up where it left off.
- Bandwidth throttle (optional): `aws configure set default.s3.max_bandwidth 25MB/s`

### When to run

Run overnight or when stepping away. The main impact is network bandwidth.
Does not lock files or interfere with local reads. At 50 Mbps upload: ~9 hours
for a full 200 GB sync.

### Verification after sync

```bash
aws s3 ls s3://s3ooi/ooinet/ --recursive --summarize | tail -3
```

Compare object count and total size against:
```bash
du -sh ~/ooi/sb/ooinet/
find ~/ooi/sb/ooinet -type f | wc -l
```

### After verification: freeing local space

Once the sync is verified complete, `~/ooi/sb/ooinet/` can be deleted locally to
reclaim ~204 GB. Redux (18 GB) and postproc remain local as working datasets.
To restore from S3 if needed:

```bash
aws s3 sync s3://s3ooi/ooinet/ ~/ooi/sb/ooinet/
```


## Localhost Data Management

### WSL virtual disk (ext4.vhdx)

WSL stores its entire Linux filesystem in a single file on C: drive:
```
C:\Users\robfa\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx
```

Key behaviors:
- The vhdx **grows** automatically as WSL writes data
- It does **not shrink** automatically when data is deleted inside WSL
- `df -h /` inside WSL reports virtual capacity, NOT actual C: drive free space
- The real constraint is C: drive free space (check with `Get-PSDrive C` in PowerShell)

### Checking actual free space

From inside WSL, `df` is misleading. Always check from Windows:
```powershell
Get-PSDrive C | ForEach-Object { "C: Free: $([math]::Round($_.Free/1GB,1)) GB" }
```

### Compacting the vhdx (reclaiming C: space after deleting data in WSL)

After deleting large amounts of data inside WSL, the vhdx retains its size on C:.
To reclaim that space:

1. Inside WSL, discard freed blocks: `sudo fstrim -v /`
2. **Close Kiro/VS Code** (it holds the vhdx open via `\\wsl.localhost\` paths)
3. Open Command Prompt **as Administrator**
4. Run:
```
wsl --shutdown
diskpart
select vdisk file="C:\Users\robfa\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx"
compact vdisk
exit
```

Important: Kiro must be closed first — its file access keeps the vhdx locked.

### When compaction is NOT needed

If you delete data inside WSL and then write new data of similar size, the vhdx
reuses the freed internal space without growing. Compaction is only needed when
you want to reclaim C: space for other Windows programs. WSL itself is not
constrained by the vhdx being "too large" — it can use all internal free space
regardless of whether the vhdx has been compacted.


### Current state (May 2026)

- `~/ooi/sb/ooinet/` deleted locally (204 GB), backed up to `s3://s3ooi/ooinet/`
- vhdx is 288 GB on disk with ~75 GB used internally (~213 GB internal headroom)
- C: drive has ~32 GB free (would be ~230 GB after successful compaction)
- WSL can write ~200 GB of new data without any C: space issues
