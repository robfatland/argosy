# Jupyter cell: CTD file overlap audit
# Identifies redundant CTD files and plots time coverage bars

import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime

print("CTD File Overlap Audit")
print("=" * 60)

BASE = Path("~/ooi/ooinet/rca/SlopeBase/scalar").expanduser()
YEARS = range(2014, 2027)

# --- Parse time range from filename ---
def parse_time_range(filename):
    """Extract start and end datetime from CTD filename."""
    pattern = r'_(\d{8}T\d{6})\.\d+-(\d{8}T\d{6})\.\d+\.nc$'
    match = re.search(pattern, filename)
    if not match:
        return None, None
    fmt = "%Y%m%dT%H%M%S"
    try:
        start = datetime.strptime(match.group(1), fmt)
        end   = datetime.strptime(match.group(2), fmt)
        return start, end
    except ValueError:
        return None, None

# --- Collect all CTD files ---
all_files = []
for year in YEARS:
    folder = BASE / f"{year}_ctd"
    if not folder.exists():
        continue
    for f in sorted(folder.glob("*.nc")):
        start, end = parse_time_range(f.name)
        if start and end:
            all_files.append({'name': f.name, 'path': f, 'start': start, 'end': end, 'year': year})

print(f"Total CTD files found: {len(all_files)}")

# --- Detect overlaps ---
# Sort by start time
all_files.sort(key=lambda x: x['start'])

overlaps = []
for i in range(len(all_files)):
    for j in range(i + 1, len(all_files)):
        a = all_files[i]
        b = all_files[j]
        # If b starts after a ends, no overlap possible for any later j
        if b['start'] >= a['end']:
            break
        # Overlap: b starts before a ends
        overlap_start = max(a['start'], b['start'])
        overlap_end   = min(a['end'],   b['end'])
        overlap_days  = (overlap_end - overlap_start).total_seconds() / 86400
        overlaps.append({
            'file_a': a['name'],
            'file_b': b['name'],
            'overlap_start': overlap_start,
            'overlap_end':   overlap_end,
            'overlap_days':  overlap_days
        })

print(f"Overlapping file pairs: {len(overlaps)}")

if overlaps:
    print(f"\nOverlap details:")
    for ov in overlaps:
        print(f"\n  A: {ov['file_a']}")
        print(f"  B: {ov['file_b']}")
        print(f"  Overlap: {ov['overlap_start'].date()} to {ov['overlap_end'].date()} ({ov['overlap_days']:.1f} days)")

# --- Identify redundant files ---
# A file is redundant if its entire time range is covered by another file
redundant = []
for i, f in enumerate(all_files):
    for j, g in enumerate(all_files):
        if i == j:
            continue
        # f is fully contained within g
        if g['start'] <= f['start'] and g['end'] >= f['end'] and f['name'] != g['name']:
            redundant.append({'redundant': f, 'covered_by': g})
            break

print(f"\nFully redundant files (entirely covered by another): {len(redundant)}")
for r in redundant:
    print(f"  REDUNDANT: {r['redundant']['name']}")
    print(f"  COVERED BY: {r['covered_by']['name']}")

# --- Strategy recommendation ---
print(f"\n{'=' * 60}")
print("STRATEGY RECOMMENDATION")
print(f"{'=' * 60}")
if len(overlaps) == 0:
    print("No overlaps detected - CTD files appear clean.")
elif len(redundant) > 0:
    total_size = sum(r['redundant']['path'].stat().st_size for r in redundant) / (1024*1024)
    print(f"Delete {len(redundant)} fully redundant files ({total_size:.1f} MB recoverable)")
    print("For partial overlaps: Keep the file with the longer time span.")
    print("\nFiles recommended for deletion:")
    for r in redundant:
        print(f"  {r['redundant']['path']}")
else:
    print(f"{len(overlaps)} partial overlaps found but no fully redundant files.")
    print("For each overlapping pair: Keep the file with the longer time span.")
    print("Partial overlaps may require trimming rather than deletion.")

# --- Plot: time coverage bars ---
print(f"\nGenerating coverage plot...")

fig, ax = plt.subplots(figsize=(14, max(4, len(all_files) * 0.25)))

# Color: red if redundant, orange if overlapping, blue otherwise
redundant_names = {r['redundant']['name'] for r in redundant}
overlap_names   = {ov['file_a'] for ov in overlaps} | {ov['file_b'] for ov in overlaps}

for i, f in enumerate(all_files):
    if f['name'] in redundant_names:
        color = 'red'
        alpha = 0.8
    elif f['name'] in overlap_names:
        color = 'orange'
        alpha = 0.7
    else:
        color = 'steelblue'
        alpha = 0.6

    ax.barh(i, (f['end'] - f['start']).total_seconds() / 86400,
            left=mdates.date2num(f['start']),
            height=0.7, color=color, alpha=alpha, edgecolor='none')

# Format x-axis as dates
ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_major_locator(mdates.YearLocator())

ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('File index (chronological)', fontsize=12)
ax.set_title(f'CTD File Time Coverage ({len(all_files)} files)\n'
             f'Blue=clean  Orange=overlapping  Red=redundant', fontsize=13)
ax.set_xlim(mdates.date2num(datetime(2014, 1, 1)),
            mdates.date2num(datetime(2026, 12, 31)))
ax.grid(True, axis='x', alpha=0.3)
ax.set_yticks([])

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='steelblue', alpha=0.6, label='Clean'),
    Patch(facecolor='orange',    alpha=0.7, label='Overlapping'),
    Patch(facecolor='red',       alpha=0.8, label='Redundant (fully covered)'),
]
ax.legend(handles=legend_elements, loc='upper left')

plt.tight_layout()
plt.savefig(Path("~/ooi/analysis/ctd_coverage.png").expanduser(), dpi=150, bbox_inches='tight')
plt.show()
print("Plot saved to ~/ooi/analysis/ctd_coverage.png")
