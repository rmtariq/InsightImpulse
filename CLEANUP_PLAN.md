# InsightPulse Cleanup Plan - Moving Unused Files to xyz_folder

## 🎯 OBJECTIVE
Move all unused/legacy files to `xyz_folder` to keep InsightPulse clean and production-ready.

---

## ✅ ACTIVE FILES (KEEP IN ROOT)

### Core Application Files
- `web_backend/simple_app.py` - Main backend server ✅ ACTIVE
- `web_frontend/simple_index.html` - Main frontend UI ✅ ACTIVE
- `backend/data_crawlers/simple_apify_adapter.py` - Data crawler ✅ ACTIVE
- `requirements.txt` - Python dependencies ✅ ACTIVE
- `.env` - Environment variables ✅ ACTIVE
- `.env.example` - Environment template ✅ ACTIVE

### Startup Scripts (KEEP)
- `start_insightpulse.sh` - Main startup script ✅ ACTIVE
- `backend.log` - Current runtime log ✅ ACTIVE

### Documentation (KEEP - ESSENTIAL)
- `README.md` - Main readme ✅ KEEP
- `START_INSIGHTPULSE.md` - Quick start guide ✅ KEEP
- `CSV_STORAGE_SUMMARY.md` - Storage docs (updated Feb 15) ✅ KEEP
- `DATA_STORAGE_STRUCTURE.md` - Storage structure (updated Feb 15) ✅ KEEP
- `HOW_TO_START.md` - Start guide ✅ KEEP

### Data Folders (KEEP - PRODUCTION DATA)
- `data/smart_crawlers/` - Raw crawled data (99 files) ✅ KEEP
- `data/analyzed/` - Sentiment analysis results (3 files) ✅ KEEP
- `data/combined/` - Combined platform data ✅ KEEP
- `data/insightpulse.db` - SQLite database ✅ KEEP

### Backend Core (KEEP)
- `backend/data_crawlers/` - All crawler code ✅ KEEP
- `backend/utils/` - Utilities (cleanup, etc.) ✅ KEEP
- `backend/services/` - AI services ✅ KEEP
- `web_backend/advanced_nlp_processor.py` - NLP engine ✅ KEEP
- `web_backend/llm_service.py` - LLM integration ✅ KEEP

---

## ❌ UNUSED FILES (MOVE TO xyz_folder)

### Legacy Documentation (30+ files)
- All proposal/brochure files (PDF, DOCX, HTML versions)
- Duplicate deployment guides
- Old testing guides
- Old strategy documents

### Legacy Code Files (20+ files)
- Old app versions (app.py, enhanced_web_app.py, etc.)
- Legacy frontend files
- Test scripts
- Old crawler implementations

### Folders to Move
- `NEImpulse/` - Old virtual environment ❌
- `framework/` - Unused framework code ❌
- `frontend/` - Old streamlit app ❌
- `crawlers/` - Duplicate crawler files ❌
- `reports/` - Old test reports (67 folders) ❌
- `reports_test/` - Test reports (3 folders) ❌
- `database/` - Unused database files ❌
- `test_data/` - Old test data ❌
- `data/csv/` - Unused ❌
- `data/json/` - Unused ❌
- `data/keywords/` - Unused ❌
- `data/processed/` - Unused ❌
- `data/workflow/` - Unused ❌
- `data/claims/` - Unused ❌
- `data/reports/` - Unused ❌
- `data/raw/` - DEPRECATED (per Feb 15 update) ❌

---

## 📋 FILES TO MOVE (Complete List)

### Documentation Files to Move (35 files)
1. INSIGHTPULSE_BROCHURE.html
2. INSIGHTPULSE_BROCHURE.md
3. INSIGHTPULSE_BROCHURE.pdf
4. INSIGHTPULSE_COMPLETE_DOCUMENTATION.md
5. InsightPulse_Complete_Proposal.md
6. InsightPulse_Comprehensive_Testing_Guide.md
7. InsightPulse_Crawling_Strategy.docx
8. InsightPulse_Final_Proposal_RM2.3M.md
9. InsightPulse_PPT_Proposal_RM1.45M.md
10. InsightPulse_Specific_Malaysian_Test_Claims.md
11. InsightPulse_Testing_Guide.html
12. Malaysian news feed.docx
13. Malaysian news feed.pdf
14. Malaysian_Claims_Testing_Demo.html
15. ADVANCED_CRAWLER_FEATURES.md
16. COMMENTS_CRAWLING_IMPLEMENTATION.md
17. COST_ANALYSIS.md
18. CRAWLING_STRATEGY.md
19. DASHBOARD_ENHANCEMENTS.md
20. DATA_NAMING_GUIDE.md
21. DEPLOYMENT_COMPLETE.md
22. DEPLOYMENT_ENHANCED.md
23. DEPLOY_NOW.md
24. Enhanced_Social_Listening_Dashboard_Features.md
25. How_to_View_Diagrams.md
26. PLATFORM_UPDATES_2026-02-10.txt
27. PROFESSIONAL_REPORTS_GUIDE.md
28. Platform_Status.txt
29. README_ENHANCED.md
30. START_HERE.txt
31. SYSTEM_STATUS.md
32. Tips_Jimat_Augment_Credit.txt
33. comprehensive_test_inputs_with_analysis_types.md
34. deployment_guide.md
35. free_deployment_tutorial.md
36. insightpulse_storage_subscription_plan.md
37. quick_test_reference.md
38. specific_test_inputs_with_crawlers.md
39. web_insightpulse_database_guide.md
40. web_insightpulse_structure.md

### Python Files to Move (30+ files)
1. app.py - Old version
2. enhanced_web_app.py - Old version
3. web_app.py - Old version
4. simple_backend.py - Duplicate
5. insightpulse_professional.py - Old version
6. ultimate_insightpulse_api.py - Old version
7. ultimate_insightpulse_frontend.py - Old version
8. ultimate_insightpulse_integration.py - Old version
9. enterprise_agentic_architecture.py - Unused
10. insightpulse_nvidia_architecture.py - Unused
11. advanced_architecture_config.py - Unused
12. main.py - Old version
13. start_app.py - Duplicate
14. start_backend.py - Duplicate
15. start_frontend.py - Duplicate
16. start_both.py - Duplicate
17. start_complete_system.py - Duplicate
18. check_deployment.py - Old
19. claim_input_system.py - Unused
20. comprehensive_testing_system.py - Unused
21. convert_to_pdf.py - Utility (move)
22. simple_pdf_converter.py - Utility (move)
23. generate_strategy_docx.py - Utility (move)
24. integrate_s_crawlers.py - Old
25. keyword_generator.py - Old
26. real_time_crawler_simulator.py - Test
27. subscription_system.py - Unused
28. sync_crawler_data.py - Unused
29. synthetic_data_generator.py - Test
30. update_raw_sentiment.py - Old
31. workflow_validator.py - Unused
32. test_*.py - All test files (15+ files)

### HTML Test Files
1. test_frontend.html
2. halal_food_test.html

### Shell Scripts to Move
1. start.sh - Duplicate
2. start_app.sh - Duplicate (keep start_insightpulse.sh)
3. deploy.sh - Old

### Config Files to Move
1. Procfile - Heroku (unused)
2. netlify.toml - Netlify (unused)
3. railway.json - Railway (unused)

### Folders to Move
1. NEImpulse/ - Old virtual environment
2. framework/ - Unused framework code
3. frontend/ - Old streamlit app
4. crawlers/ - Duplicate crawler files
5. reports/ - 67 test report folders
6. reports_test/ - 3 test folders
7. database/ - Unused database
8. test_data/ - Test data
9. .zencoder/ - IDE config
10. .zenflow/ - IDE config
11. .pytest_cache/ - Test cache
12. __pycache__/ - Python cache

### Data Folders to Move
1. data/csv/ - Unused
2. data/json/ - Unused
3. data/keywords/ - Unused
4. data/processed/ - Unused
5. data/workflow/ - Unused
6. data/claims/ - Unused
7. data/reports/ - Unused
8. data/raw/ - DEPRECATED (Feb 15, 2026)

### Web Frontend Files to Move (Keep only simple_index.html)
1. web_frontend/index.html - Old version
2. web_frontend/premium_dashboard.html - Unused
3. web_frontend/query_processing_dashboard.html - Unused
4. web_frontend/keyword_breakdown_demo.html - Unused
5. web_frontend/simple_professional.html - Old
6. web_frontend/test_simple.html - Test
7. web_frontend/test_visualization_dashboard.html - Test
8. web_frontend/universal_dashboard.html - Old

### Web Backend Files to Move
1. web_backend/app.py - Old version (keep simple_app.py)
2. web_backend/real_ai_analysis.py - Unused
3. web_backend/real_crawler_integration.py - Unused
4. web_backend/config.py - Check if used
5. web_backend/data/ - Check if used

### Log Files
1. backend.log - Keep current, move old
2. server_debug.log - Move
3. test.log - Move
4. test_full_analysis_output.log - Move
5. test_real_query_output.log - Move

---

## 🚀 CLEAN STRUCTURE AFTER CLEANUP

```
InsightPulse/
├── .env                                    # Environment variables
├── .env.example                            # Template
├── requirements.txt                        # Dependencies
├── README.md                              # Main readme
├── START_INSIGHTPULSE.md                  # Quick start
├── HOW_TO_START.md                        # Start guide
├── CSV_STORAGE_SUMMARY.md                 # Storage docs
├── DATA_STORAGE_STRUCTURE.md              # Storage structure
├── start_insightpulse.sh                  # Main startup script
├── backend.log                            # Current log
├── backend/                               # Backend code
│   ├── data_crawlers/                     # All crawlers
│   │   └── simple_apify_adapter.py        # Main adapter
│   ├── utils/                             # Utilities
│   │   └── data_cleanup.py                # Cleanup utility
│   └── services/                          # AI services
├── web_backend/                           # Web backend
│   ├── simple_app.py                      # Main backend ✅
│   ├── advanced_nlp_processor.py          # NLP engine
│   └── llm_service.py                     # LLM service
├── web_frontend/                          # Web frontend
│   └── simple_index.html                  # Main UI ✅
├── data/                                  # Data storage
│   ├── smart_crawlers/                    # Raw data (99 files)
│   ├── analyzed/                          # Analyzed data (3 files)
│   ├── combined/                          # Combined data
│   └── insightpulse.db                    # Database
└── xyz_folder/                            # Archive (120+ files)
    ├── old_docs/
    ├── old_code/
    ├── old_tests/
    ├── old_reports/
    └── deprecated/
```

---

## 📊 CLEANUP STATISTICS

**Before Cleanup:**
- Total files: 200+ files
- Documentation: 40+ files
- Code files: 50+ files
- Test files: 20+ files
- Reports: 70+ folders
- Structure: Complex

**After Cleanup:**
- Active files: ~20 files
- Clean structure: 5 main folders
- Easy to navigate
- Production-ready ✅

---

**Ready to execute cleanup? All files will be safely moved to `xyz_folder/` for backup.**
