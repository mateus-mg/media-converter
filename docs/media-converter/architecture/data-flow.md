# Data Flow

## Conversion Flow

```mermaid
flowchart TD
    A[User Input] --> B{File or Directory?}
    B -->|File| C[Single File Mode]
    B -->|Directory| D[Batch Mode]
    C --> E[Hardware Detection]
    D --> E
    E --> F{NVIDIA Available?}
    F -->|Yes| G[NVENC Encoder]
    F -->|No| H{Intel QSV Available?}
    H -->|Yes| I[QSV Encoder]
    H -->|No| J[Software Encoder]
    G --> K[Video Info via ffprobe]
    I --> K
    J --> K
    K --> L{H.265/HEVC Codec?}
    L -->|No| M[Skip - not HEVC]
    L -->|Yes| N[CRF Calculation]
    N --> O[FFmpeg Conversion]
```

## Quality Selection Logic

CRF is automatically calculated based on source bitrate:

| Bitrate | CRF | Use Case |
|---------|-----|----------|
| < 10 Mbps | 18-19 | Preserve details in low bitrate sources |
| 10-25 Mbps | 20-21 | Balanced |
| 25-50 Mbps | 22-23 | Control size for high bitrate |
| > 50 Mbps | 23-24 | Prioritize size control |

Adjustments:
- 4K: +1 CRF (more compression)
- 720p or lower: -1 CRF (preserve quality)
- High FPS (≥50): -1 CRF (preserve detail)