# Graph Report - RAG  (2026-11-02)

## Corpus Check
- 4 files · ~1,582 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: .example 1, (none) 1)

## Summary
- 40 nodes · 66 edges · 6 communities (3 shown, 3 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- app.py
- analyze_meal
- MealAnalysis
- 🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)
- load_image

## God Nodes (most connected - your core abstractions)
1. `analyze_meal()` - 11 edges
2. `MealAnalysis` - 9 edges
3. `MealAnalysisError` - 8 edges
4. `load_image()` - 7 edges
5. `main()` - 7 edges
6. `_get_client()` - 6 edges
7. `render_results()` - 6 edges
8. `هيكل المشروع` - 6 edges
9. `🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)` - 5 edges
10. `FoodItem` - 4 edges

## Surprising Connections (you probably didn't know these)
- `هيكل المشروع` --references--> `load_image()`  [INFERRED]
  README.md → ai_service.py
- `هيكل المشروع` --references--> `analyze_meal()`  [INFERRED]
  README.md → ai_service.py
- `هيكل المشروع` --references--> `FoodItem`  [INFERRED]
  README.md → ai_service.py
- `هيكل المشروع` --references--> `MealAnalysis`  [INFERRED]
  README.md → ai_service.py
- `هيكل المشروع` --references--> `render_results()`  [INFERRED]
  README.md → app.py

## Import Cycles
- None detected.

## Communities (6 total, 3 thin omitted)

### Community 2 - "analyze_meal"
Cohesion: 0.29
Nodes (3): analyze_meal(), _get_client(), _sanitize()

### Community 3 - "MealAnalysis"
Cohesion: 0.32
Nodes (4): FoodItem, MealAnalysis, render_results(), هيكل المشروع

### Community 4 - "🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)"
Cohesion: 0.40
Nodes (4): التشغيل, المزايا, خريطة المعرفة (Graphify), 🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `هيكل المشروع` connect `MealAnalysis` to `analyze_meal`, `🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)`, `load_image`?**
  _High betweenness centrality (0.263) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `MealAnalysis` (e.g. with `main()` and `render_results()`) actually correct?**
  _`MealAnalysis` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Why does `analyze_meal()` connect `analyze_meal` to `ai_service.py`, `app.py`, `MealAnalysis`, `load_image`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `main()` (e.g. with `MealAnalysis` and `MealAnalysisError`) actually correct?**
  _`main()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Why does `🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)` connect `🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)` to `MealAnalysis`?**
  _High betweenness centrality (0.197) - this node is a cross-community bridge._