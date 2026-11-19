# Ablation `ablation-minne`: används minnet?

Sista generationens bästa drottning, 10 kolonieliv per läge, 12000 tick, läge baldwin. Fruset minne = cellerna förblir 0 hela livet. Samma problem och frön i båda lägena.

| körning | n | lösta, minne på | lösta, fruset minne | mat, på | mat, fruset |
|---|---|---|---|---|---|
| evo-baldwin-mem4 | 24 | 5 | 0 | 46068 | 36514 |
| evo-baldwin-mem4-s2 | 14 | 0 | 0 | 26004 | 25922 |
| evo-baldwin-mem4-s3 | 18 | 5 | 4 | 36905 | 38850 |
| evo-baldwin-mem4-s4 | 12 | 0 | 0 | 26265 | 21763 |
| evo-baldwin-mem4-s5 | 24 | 3 | 1 | 46254 | 27739 |

Minnet på löser fler i 3 körningar, färre i 0, lika i 2. Löser drottningarna lika mycket med fruset minne används minnet inte till något.
