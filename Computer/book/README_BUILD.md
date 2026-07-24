# EPUB 빌드 방법

Pandoc 3.x 기준:

```bash
cd book
pandoc \
  00_preface.md 01_history_computation.md 02_digital_logic_architecture.md \
  03_os_concurrency_memory.md 04_languages_compilers.md 05_algorithms_data.md \
  06_networks_databases_distributed.md 07_software_architecture.md \
  08_quality_debug_performance.md 09_security_reliability.md \
  10_game_graphics_ai.md 11_capstone_curriculum.md 12_workbook.md \
  13_selected_solutions.md 14_bibliography.md \
  --metadata-file=metadata.yaml --css=epub.css \
  --epub-cover-image=cover.png --toc --toc-depth=3 --split-level=1 \
  --resource-path=. -o ../dist/Computer_End_to_End_Programmer_KO.epub
```

`cover.png`과 `diagrams/*.png`는 EPUB에 포함된다. 외부 논문 URL은 온라인 접근이 필요한 참고 링크다.
