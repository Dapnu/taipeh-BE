"""
Models endpoint - Available ML models for route prediction
"""

from fastapi import APIRouter, status
from typing import List
from app.schemas.model import ModelInfo

router = APIRouter()


# Data model yang tersedia untuk route prediction
AVAILABLE_MODELS = [
    # Tree-based Models
    ModelInfo(
        id="decision_tree",
        name="Decision Tree",
        category="tree",
        description="Model berbasis pohon keputusan yang membuat prediksi dengan membagi data berdasarkan fitur-fitur tertentu.",
        how_it_works="Membangun struktur pohon dengan membagi data pada setiap node berdasarkan fitur yang memberikan information gain terbaik. Setiap leaf node merepresentasikan prediksi akhir.",
        strengths=[
            "Mudah diinterpretasi dan divisualisasikan",
            "Tidak memerlukan normalisasi data",
            "Dapat menangani data kategorikal dan numerik",
            "Cepat untuk training dan prediksi"
        ],
        use_cases=[
            "Baseline model untuk perbandingan",
            "Analisis fitur penting dalam rute",
            "Prediksi cepat dengan data terbatas"
        ],
        complexity="low",
        accuracy_level="basic",
        training_time="1-3 menit",
        is_available=True
    ),
    ModelInfo(
        id="random_forest",
        name="Random Forest",
        category="tree",
        description="Ensemble learning yang menggabungkan banyak decision trees untuk meningkatkan akurasi dan mengurangi overfitting.",
        how_it_works="Membuat banyak decision trees dengan random sampling data dan fitur (bagging). Prediksi akhir adalah rata-rata dari semua trees untuk regresi atau voting untuk klasifikasi.",
        strengths=[
            "Akurasi tinggi dan robust terhadap overfitting",
            "Dapat menangani missing values",
            "Memberikan feature importance ranking",
            "Parallel processing untuk training cepat"
        ],
        use_cases=[
            "Prediksi durasi perjalanan standar",
            "Identifikasi faktor penting (jarak, waktu, cuaca)",
            "Handling data dengan noise"
        ],
        complexity="medium",
        accuracy_level="intermediate",
        training_time="5-10 menit",
        is_available=True
    ),
    ModelInfo(
        id="gradient_boosting",
        name="Gradient Boosting (XGBoost)",
        category="tree",
        description="Ensemble method yang membangun trees secara sequential, setiap tree memperbaiki error dari tree sebelumnya.",
        how_it_works="Melatih trees secara berurutan dimana setiap tree baru fokus memperbaiki residual error dari ensemble sebelumnya. Menggunakan gradient descent untuk optimasi.",
        strengths=[
            "Akurasi sangat tinggi untuk data tabular",
            "Built-in regularization untuk prevent overfitting",
            "Efisien dengan sparse data",
            "Handling missing values otomatis"
        ],
        use_cases=[
            "Prediksi akurat untuk rute kompleks",
            "Kompetisi dan production-grade predictions",
            "Data dengan banyak fitur interaksi"
        ],
        complexity="medium",
        accuracy_level="advanced",
        training_time="10-20 menit",
        is_available=True
    ),
    
    # Linear Models
    ModelInfo(
        id="linear_regression",
        name="Linear Regression",
        category="linear",
        description="Model statistik dasar yang memodelkan hubungan linear antara fitur input dan target output.",
        how_it_works="Menemukan koefisien optimal untuk setiap fitur yang meminimalkan sum of squared errors. Formula: y = β₀ + β₁x₁ + β₂x₂ + ... + βₙxₙ",
        strengths=[
            "Sangat cepat untuk training dan inference",
            "Interpretable - koefisien menunjukkan pengaruh fitur",
            "Bekerja baik untuk hubungan linear",
            "Low memory footprint"
        ],
        use_cases=[
            "Baseline model sederhana",
            "Prediksi cepat real-time",
            "Rute dengan pola linear (jarak vs waktu)"
        ],
        complexity="low",
        accuracy_level="basic",
        training_time="< 1 menit",
        is_available=True
    ),
    ModelInfo(
        id="ridge_regression",
        name="Ridge Regression (L2)",
        category="linear",
        description="Linear regression dengan L2 regularization untuk mengurangi overfitting pada fitur yang berkorelasi.",
        how_it_works="Menambahkan penalty term (λ∑β²) pada loss function untuk mencegah koefisien terlalu besar. Bagus untuk multicollinearity.",
        strengths=[
            "Mengatasi multicollinearity antar fitur",
            "Lebih stabil dari linear regression biasa",
            "Prevent overfitting pada data dengan banyak fitur",
            "Semua fitur tetap dipertahankan"
        ],
        use_cases=[
            "Data dengan fitur berkorelasi tinggi",
            "Prediksi dengan banyak variabel traffic",
            "Model yang perlu semua fitur"
        ],
        complexity="low",
        accuracy_level="basic",
        training_time="< 1 menit",
        is_available=True
    ),
    ModelInfo(
        id="lasso_regression",
        name="Lasso Regression (L1)",
        category="linear",
        description="Linear regression dengan L1 regularization yang dapat melakukan automatic feature selection.",
        how_it_works="Menambahkan penalty term (λ∑|β|) yang dapat membuat beberapa koefisien menjadi nol, efektif melakukan feature selection.",
        strengths=[
            "Automatic feature selection",
            "Model lebih sparse dan interpretable",
            "Bagus untuk data dengan banyak fitur tidak relevan",
            "Mengurangi dimensi model"
        ],
        use_cases=[
            "Feature selection otomatis",
            "Identifikasi fitur paling penting",
            "Model sederhana dengan fitur minimal"
        ],
        complexity="low",
        accuracy_level="basic",
        training_time="< 1 menit",
        is_available=True
    ),
    
    # Temporal Models
    ModelInfo(
        id="lstm",
        name="LSTM (Long Short-Term Memory)",
        category="temporal",
        description="Recurrent Neural Network yang dapat mempelajari pola temporal jangka panjang dengan cell state dan gating mechanisms.",
        how_it_works="Menggunakan forget gate, input gate, dan output gate untuk mengontrol informasi yang mengalir melalui cell state. Dapat mengingat informasi jangka panjang dan melupakan yang tidak relevan.",
        strengths=[
            "Menangkap dependencies temporal jangka panjang",
            "Tidak terkena vanishing gradient problem",
            "Efektif untuk sequence prediction",
            "Dapat model pola traffic kompleks sepanjang waktu"
        ],
        use_cases=[
            "Prediksi berdasarkan pola historis traffic",
            "Forecasting traffic jam waktu tertentu",
            "Time-series route duration prediction",
            "Pola commute pagi/sore hari"
        ],
        complexity="high",
        accuracy_level="advanced",
        training_time="30-60 menit",
        is_available=True
    ),
    ModelInfo(
        id="gru",
        name="GRU (Gated Recurrent Unit)",
        category="temporal",
        description="Simplified version dari LSTM dengan arsitektur lebih sederhana namun performa comparable. Lebih cepat untuk train.",
        how_it_works="Menggunakan update gate dan reset gate (2 gates vs 3 di LSTM). Update gate mengontrol informasi dari past, reset gate mengontrol berapa banyak past information dilupakan.",
        strengths=[
            "Lebih cepat train dibanding LSTM",
            "Parameter lebih sedikit (lebih efisien memory)",
            "Performa hampir sama dengan LSTM",
            "Cocok untuk real-time applications"
        ],
        use_cases=[
            "Real-time traffic prediction",
            "Prediksi dengan computational constraint",
            "Pola temporal dengan sequence pendek-menengah",
            "Mobile/edge deployment"
        ],
        complexity="high",
        accuracy_level="advanced",
        training_time="20-40 menit",
        is_available=True
    ),
    ModelInfo(
        id="temporal_cnn",
        name="Temporal CNN (1D Convolution)",
        category="temporal",
        description="Convolutional Neural Network untuk data temporal yang mengekstrak pola lokal dalam time series.",
        how_it_works="Menggunakan 1D convolution filters yang slide sepanjang time axis untuk mendeteksi local patterns. Lebih cepat dari RNN karena parallel computation.",
        strengths=[
            "Training lebih cepat dari LSTM/GRU",
            "Parallel computation (tidak sequential)",
            "Bagus untuk pattern recognition dalam time windows",
            "Efisien untuk inference"
        ],
        use_cases=[
            "Deteksi pola traffic berulang",
            "Rush hour pattern recognition",
            "Fast temporal predictions",
            "Pattern-based route selection"
        ],
        complexity="medium",
        accuracy_level="intermediate",
        training_time="10-20 menit",
        is_available=True
    ),
    
    # Spatio-Temporal Models
    ModelInfo(
        id="gnn",
        name="GNN (Graph Neural Network)",
        category="spatio_temporal",
        description="Neural network yang bekerja pada struktur graph untuk mempelajari relationships antar nodes (lokasi/intersections).",
        how_it_works="Merepresentasikan road network sebagai graph dimana nodes adalah intersections dan edges adalah roads. Message passing antar nodes untuk aggregate informasi dari neighbors.",
        strengths=[
            "Model spatial relationships antar lokasi",
            "Capture network structure secara natural",
            "Dapat propagate traffic information",
            "Memahami connectivity patterns"
        ],
        use_cases=[
            "Network-wide traffic prediction",
            "Multi-route optimization",
            "Understanding traffic flow propagation",
            "City-scale route planning"
        ],
        complexity="high",
        accuracy_level="advanced",
        training_time="45-90 menit",
        is_available=True
    ),
    ModelInfo(
        id="gman",
        name="GMAN (Graph Multi-Attention Network)",
        category="spatio_temporal",
        description="State-of-the-art model yang menggabungkan graph convolution, temporal attention, dan spatial attention untuk spatio-temporal prediction.",
        how_it_works="Menggunakan spatial attention untuk menangkap dynamic spatial correlations, temporal attention untuk dependencies antar time steps, dan transform attention untuk external factors (weather, events).",
        strengths=[
            "Capture spatio-temporal dependencies secara simultan",
            "Attention mechanism untuk interpretability",
            "Dapat incorporate external factors",
            "State-of-the-art accuracy untuk traffic forecasting"
        ],
        use_cases=[
            "Advanced traffic forecasting",
            "Multi-factor route prediction (weather, events)",
            "Long-term traffic planning",
            "Research dan maximum accuracy scenarios"
        ],
        complexity="high",
        accuracy_level="advanced",
        training_time="60-120 menit",
        is_available=True
    ),
    ModelInfo(
        id="stgcn",
        name="STGCN (Spatio-Temporal Graph Convolutional Network)",
        category="spatio_temporal",
        description="Model yang menggabungkan graph convolution untuk spatial dependencies dan 1D convolution untuk temporal patterns.",
        how_it_works="Spatial: Graph convolution untuk aggregate neighbor information. Temporal: 1D CNN untuk capture temporal patterns. Layer stacking untuk multi-scale learning.",
        strengths=[
            "Efficient spatio-temporal modeling",
            "Faster training dari pure attention models",
            "Capture local spatial dan temporal patterns",
            "Good balance antara accuracy dan speed"
        ],
        use_cases=[
            "Regional traffic prediction",
            "Medium to large scale deployments",
            "Real-time spatio-temporal forecasting",
            "Production systems dengan accuracy requirement tinggi"
        ],
        complexity="high",
        accuracy_level="advanced",
        training_time="40-80 menit",
        is_available=True
    ),
    ModelInfo(
        id="astgcn",
        name="ASTGCN (Attention-based STGCN)",
        category="spatio_temporal",
        description="Enhanced STGCN dengan spatial attention dan temporal attention untuk adaptive learning dari spatio-temporal patterns.",
        how_it_works="Menambahkan attention layers pada STGCN untuk dynamically focus pada relevant spatial locations dan time periods. Multi-component: recent, daily-periodic, weekly-periodic.",
        strengths=[
            "Adaptive spatial-temporal modeling",
            "Capture periodic patterns (daily, weekly)",
            "Better interpretability dengan attention weights",
            "Robust untuk data dengan varying patterns"
        ],
        use_cases=[
            "Complex urban traffic with multiple patterns",
            "Holiday dan weekday differentiation",
            "Event-aware traffic prediction",
            "High-accuracy production systems"
        ],
        complexity="high",
        accuracy_level="advanced",
        training_time="50-100 menit",
        is_available=True
    )
]


@router.get(
    "/models",
    response_model=List[ModelInfo],
    status_code=status.HTTP_200_OK,
    summary="Get Available ML Models",
    description="Retrieve list of all available machine learning models for route prediction with detailed information"
)
async def get_available_models(
    category: str | None = None
) -> List[ModelInfo]:
    """
    Get list of available ML models for route prediction
    
    Args:
        category: Optional filter by model category (tree, linear, temporal, spatio_temporal)
    
    Returns:
        List of ModelInfo objects with details about each model
    """
    if category:
        return [model for model in AVAILABLE_MODELS if model.category == category]
    return AVAILABLE_MODELS


@router.get(
    "/models/{model_id}",
    response_model=ModelInfo,
    status_code=status.HTTP_200_OK,
    summary="Get Model Details",
    description="Get detailed information about a specific model"
)
async def get_model_details(model_id: str) -> ModelInfo:
    """
    Get detailed information about a specific model
    
    Args:
        model_id: ID of the model to retrieve
    
    Returns:
        ModelInfo object with model details
    """
    from fastapi import HTTPException
    
    model = next((m for m in AVAILABLE_MODELS if m.id == model_id), None)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model with id '{model_id}' not found"
        )
    return model


@router.get(
    "/models/categories",
    status_code=status.HTTP_200_OK,
    summary="Get Model Categories",
    description="Get list of available model categories"
)
async def get_model_categories():
    """Get list of model categories with counts"""
    categories = {}
    for model in AVAILABLE_MODELS:
        if model.category not in categories:
            categories[model.category] = {
                "name": model.category,
                "count": 0,
                "models": []
            }
        categories[model.category]["count"] += 1
        categories[model.category]["models"].append({
            "id": model.id,
            "name": model.name
        })
    
    return {
        "total_models": len(AVAILABLE_MODELS),
        "categories": list(categories.values())
    }
