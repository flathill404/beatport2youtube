# (☝︎ ՞ਊ ՞)☝︎

```bash
python src/main.py
```

```bash
cat 202508301426JST.json | jq -r '.results[] | [.isrc, .name + " " +.mix_name] | @tsv'
```
