# Third-party components

This repository contains assembly code and original configuration only. Downloaded binaries and shaders are ignored by Git and recorded in sources.lock.json. Local assembly is not a grant of permission to redistribute a combined binary archive.

- DLSS5-Feeder: https://github.com/jlrouzies-fr/DLSS5-Feeder (v1.19.0). Preserve its license when distributing covered components.
- ReShade: https://github.com/crosire/reshade (6.8.0), BSD license. The 64-bit helper uses the official full-addon build; the game uses the existing separate custom Crabe build.
- LumeniteFX: https://github.com/umar-afzaal/LumeniteFX, AGNYA license; retained license/notice in assembled package. Check those terms before distribution.
- ReShade framework headers: https://github.com/crosire/reshade-shaders, retained licenses.
- NVIDIA NGX DLSS and modified neural runtime: proprietary NVIDIA components. RTX40 archive is a community-modified binary from RankFTW/rhi-repo; matching release hashes establish download integrity, not NVIDIA endorsement or a security audit.
- RenoDX neural addon: community build mirrored by RankFTW/rhi-repo. Source/redistribution permission for this specific addon has not been established.

For sharing, distribute this source/installer repository and have recipients fetch the pinned dependencies locally. Do not publish the locally assembled binaries as an all-in-one mod without resolving their distribution terms.
