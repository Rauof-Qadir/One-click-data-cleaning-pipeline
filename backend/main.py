from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cleaning_pipeline.file_ingestion_and_parsing1 import router as upload_router
from cleaning_pipeline.initial_data_profiling2 import router as transform_router
from cleaning_pipeline.table_structure_and_headers3 import router as trim_router
from cleaning_pipeline.text_and_string_cleaning4 import router as text_std_router
from cleaning_pipeline.datatype_and_formateconversion5 import router as type_inf_router
from cleaning_pipeline.missing_value_imputation6 import router as missing_imp_router
from cleaning_pipeline.duplicate_resolution import router as duplicate_res_router
from cleaning_pipeline.numeric_validation_outliers import router as numeric_val_router
from cleaning_pipeline.categorical_standardization import router as cat_std_router
from cleaning_pipeline.temporal_validation import router as temporal_val_router
from cleaning_pipeline.domain_validation import router as domain_val_router
from cleaning_pipeline.cross_column_consistency import router as cross_col_router
from cleaning_pipeline.anomaly_detection import router as anomaly_router
from cleaning_pipeline.final_qa_verification import router as final_qa_router
from cleaning_pipeline.reporting_export import router as reporting_router














app = FastAPI(title="Data Cleaning Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)

# Naya transformation wala route connect kar diya
app.include_router(transform_router)

app.include_router(trim_router)

app.include_router(text_std_router)


app.include_router(type_inf_router)

app.include_router(missing_imp_router)

app.include_router(duplicate_res_router)

app.include_router(numeric_val_router)

app.include_router(cat_std_router)

app.include_router(temporal_val_router)

app.include_router(domain_val_router)

app.include_router(cross_col_router)

app.include_router(anomaly_router)

app.include_router(final_qa_router)

app.include_router(reporting_router)

@app.get("/")
def home():
    return {"message": "Data Cleaning Pipeline API is running"}
