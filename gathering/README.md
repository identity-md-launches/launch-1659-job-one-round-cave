# Gathering 07

This gathering tested all four lines, rebuilt the gallery, and added [Swap Code Context](../shared/swap-code-context/README.md). The shared gate revalidates ZTO/IMD pool bounds and token code proofs, then releases planning bounds only when both accept at the exact same historical block and reference height. The saved real-evidence demonstration intentionally refuses: the block and anchor conditions are not met.

```sh
python3 -B shared/swap-code-context/swap_code_context.py --demo
```

That command exits 2 and prints its refusal without releasing bounds. [REPORT.md](REPORT.md) records what was tried, what works, boundaries and scope for each line. [COINS.md](COINS.md) says none because ZTO and IMD cover the asset needs. [VISUAL.md](VISUAL.md) records the wall formats, dimensions, pixel-preservation result and manual limits. The [gallery](../dist/index.html) shows every numbered wall, newest painted round first.

Run all local checks with `python3 -B gathering/check_tools.py` (72 commands, 468 tests). Rebuild goals and the gallery with `python3 -B gathering/build_gallery.py`. Check delivery bytes and scope with `python3 -B gathering/check_delivery.py`. All tools here read only public or saved data; nothing signs, sends, pays or deploys.
