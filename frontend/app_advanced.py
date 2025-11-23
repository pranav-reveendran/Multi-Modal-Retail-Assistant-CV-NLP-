"""
Advanced Streamlit Frontend for Multi-Modal Retail Assistant
Enhanced UI with hybrid search, filtering, analytics, and better UX
"""

import streamlit as st
import requests
from PIL import Image
import io
import os
from typing import List, Dict, Optional
import plotly.express as px
import plotly.graph_objects as go


# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")


# Page configuration
st.set_page_config(
    page_title="Multi-Modal Retail Assistant (Advanced)",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stImage {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .stImage:hover {
        transform: scale(1.05);
    }
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }
    .similarity-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    .price-tag {
        background-color: #10b981;
        color: white;
        padding: 5px 12px;
        border-radius: 15px;
        font-size: 18px;
        font-weight: bold;
    }
    .category-badge {
        background-color: #3b82f6;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    h1 {
        color: #1f2937;
        font-weight: 800;
    }
    h2, h3 {
        color: #374151;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f3f4f6;
        border-radius: 10px;
        padding: 0px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if API is available"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except:
        return False, None


def get_categories():
    """Fetch available categories"""
    try:
        response = requests.get(f"{API_URL}/categories", timeout=5)
        if response.status_code == 200:
            return response.json()['categories']
        return []
    except:
        return []


def get_price_range():
    """Fetch price range"""
    try:
        response = requests.get(f"{API_URL}/price-range", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['min_price'], data['max_price']
        return 0.0, 100.0
    except:
        return 0.0, 100.0


def get_stats():
    """Fetch analytics statistics"""
    try:
        response = requests.get(f"{API_URL}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def search_hybrid(image_file=None, text=None, k=5, alpha=0.5, category=None, min_price=None, max_price=None, rerank=True):
    """Hybrid search API call"""
    try:
        files = {}
        if image_file:
            files = {"file": image_file}

        data = {
            "text": text,
            "k": k,
            "alpha": alpha,
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "rerank": rerank
        }

        response = requests.post(
            f"{API_URL}/search/hybrid",
            files=files if files else None,
            data={k: v for k, v in data.items() if v is not None},
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None

    except Exception as e:
        st.error(f"Error: {e}")
        return None


def search_by_image(image_file, k=5, search_mode="image", category=None, min_price=None, max_price=None):
    """Image search API call"""
    try:
        files = {"file": image_file}
        params = {
            "k": k,
            "search_mode": search_mode,
            "category": category,
            "min_price": min_price,
            "max_price": max_price
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.post(
            f"{API_URL}/search/image",
            files=files,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception as e:
        st.error(f"Error: {e}")
        return None


def search_by_text(query, k=5, search_mode="text", category=None, min_price=None, max_price=None, rerank=True):
    """Text search API call"""
    try:
        payload = {
            "query": query,
            "k": k,
            "search_mode": search_mode,
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "rerank": rerank
        }

        response = requests.post(
            f"{API_URL}/search/text",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception as e:
        st.error(f"Error: {e}")
        return None


def display_product_card(product: Dict, col):
    """Enhanced product card display"""
    with col:
        # Image
        image_path = product.get('image_path', '')
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                st.image(img, use_container_width=True)
            except:
                st.info("📷 Image unavailable")
        else:
            st.info("📷 Image unavailable")

        # Product info in a styled container
        st.markdown('<div class="product-card">', unsafe_allow_html=True)

        # Title
        st.markdown(f"**{product.get('title', 'N/A')}**")

        # Category badge
        category = product.get('category', 'N/A')
        st.markdown(
            f'<span class="category-badge">{category}</span>',
            unsafe_allow_html=True
        )

        # Brand
        if 'brand' in product and product['brand']:
            st.caption(f"🏷️ {product['brand']}")

        # Price
        price = product.get('price', 0)
        st.markdown(
            f'<div class="price-tag">${price:.2f}</div>',
            unsafe_allow_html=True
        )

        # Scores
        sim_score = product.get('similarity_score', 0)
        st.markdown(
            f'<div class="similarity-badge">Match: {sim_score*100:.1f}%</div>',
            unsafe_allow_html=True
        )

        if 'rerank_score' in product:
            rerank = product['rerank_score']
            st.caption(f"🎯 Rerank Score: {rerank:.3f}")

        # Description
        if 'description' in product and product['description']:
            with st.expander("📝 Description"):
                st.write(product['description'])

        # Additional attributes
        if 'color' in product and product['color']:
            st.caption(f"🎨 Color: {product['color']}")

        if 'season' in product and product['season']:
            st.caption(f"🌤️ Season: {product['season']}")

        st.markdown('</div>', unsafe_allow_html=True)


def main():
    """Main application"""

    # Header
    st.markdown("# 🛍️ Multi-Modal Retail Assistant")
    st.markdown("### *Advanced Search with AI-Powered Recommendations*")

    # Check API
    api_ok, health_data = check_api_health()

    if not api_ok:
        st.error("⚠️ Backend API unavailable. Start server:")
        st.code("cd backend && uvicorn main_advanced:app --reload")
        return

    st.success(f"✅ Connected | {health_data.get('num_products', 0)} products loaded")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Search Settings")

        # Search mode selection
        search_tabs = st.radio(
            "Search Mode:",
            ["🖼️ Image", "📝 Text", "🔀 Hybrid"],
            horizontal=True
        )

        st.markdown("---")

        # Common settings
        num_results = st.slider(
            "Number of Results",
            min_value=1,
            max_value=20,
            value=6,
            help="How many products to show"
        )

        # Advanced filters
        st.markdown("### 🎯 Filters")

        # Category filter
        categories = get_categories()
        category_filter = st.selectbox(
            "Category",
            options=["All"] + categories,
            help="Filter by product category"
        )
        category_filter = None if category_filter == "All" else category_filter

        # Price filter
        min_price, max_price = get_price_range()
        price_range = st.slider(
            "Price Range ($)",
            min_value=float(min_price),
            max_value=float(max_price),
            value=(float(min_price), float(max_price))
        )

        # Hybrid settings
        if "Hybrid" in search_tabs:
            st.markdown("### 🔀 Hybrid Settings")
            alpha = st.slider(
                "Image Weight",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="0=text only, 1=image only"
            )
        else:
            alpha = 0.5

        # Reranking
        use_reranking = st.checkbox(
            "Enable Reranking",
            value=True,
            help="Use cross-encoder for better results (slower)"
        )

        st.markdown("---")

        # Analytics
        if st.button("📊 View Analytics"):
            st.session_state.show_analytics = True

        # About
        st.markdown("### ℹ️ About")
        st.caption("""
        Advanced multi-modal search with:
        - 🎨 Hybrid image+text queries
        - 🎯 Smart filtering
        - ⚡ Fast caching
        - 🧠 AI reranking
        """)

    # Main content
    if "Hybrid" in search_tabs:
        st.header("🔀 Hybrid Search")
        st.markdown("Combine image and text for powerful multi-modal search")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Upload Image (Optional)")
            uploaded_image = st.file_uploader(
                "Choose an image...",
                type=["jpg", "jpeg", "png"],
                label_visibility="collapsed"
            )

            if uploaded_image:
                image = Image.open(uploaded_image)
                st.image(image, caption="Query Image", use_container_width=True)

        with col2:
            st.subheader("Enter Text (Optional)")
            text_query = st.text_area(
                "Describe what you're looking for...",
                placeholder="e.g., 'blue running shoes with white stripes'",
                height=150,
                label_visibility="collapsed"
            )

        if st.button("🔍 Search", type="primary", use_container_width=True):
            if not uploaded_image and not text_query:
                st.warning("Please provide an image, text, or both!")
            else:
                with st.spinner("Searching..."):
                    results = search_hybrid(
                        image_file=uploaded_image,
                        text=text_query if text_query else None,
                        k=num_results,
                        alpha=alpha,
                        category=category_filter,
                        min_price=price_range[0],
                        max_price=price_range[1],
                        rerank=use_reranking
                    )

                    if results and results.get('results'):
                        st.success(f"✅ Found {results['num_results']} products in {results.get('latency_ms', 0):.0f}ms")

                        # Display results
                        st.subheader("Search Results")
                        products = results['results']

                        cols_per_row = 3
                        for i in range(0, len(products), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                if i + j < len(products):
                                    display_product_card(products[i + j], col)
                    else:
                        st.warning("No results found")

    elif "Image" in search_tabs:
        st.header("🖼️ Image Search")
        st.markdown("Upload a product image to find visually similar items")

        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=["jpg", "jpeg", "png"]
        )

        if uploaded_file:
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("Your Image")
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)

            if st.button("🔍 Search", type="primary", use_container_width=True):
                with st.spinner("Analyzing image..."):
                    results = search_by_image(
                        uploaded_file,
                        k=num_results,
                        category=category_filter,
                        min_price=price_range[0],
                        max_price=price_range[1]
                    )

                    if results and results.get('results'):
                        st.success(f"✅ Found {results['num_results']} products in {results.get('latency_ms', 0):.0f}ms")

                        st.subheader("Similar Products")
                        products = results['results']

                        cols_per_row = 3
                        for i in range(0, len(products), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                if i + j < len(products):
                                    display_product_card(products[i + j], col)
                    else:
                        st.warning("No results found")

    else:  # Text search
        st.header("📝 Text Search")
        st.markdown("Describe what you're looking for in natural language")

        query = st.text_input(
            "Search query",
            placeholder="e.g., 'red summer dress', 'nike running shoes'",
            label_visibility="collapsed"
        )

        if st.button("🔍 Search", type="primary", use_container_width=True) and query:
            with st.spinner("Searching..."):
                results = search_by_text(
                    query,
                    k=num_results,
                    category=category_filter,
                    min_price=price_range[0],
                    max_price=price_range[1],
                    rerank=use_reranking
                )

                if results and results.get('results'):
                    st.success(f"✅ Found {results['num_results']} products in {results.get('latency_ms', 0):.0f}ms")

                    st.subheader("Matching Products")
                    products = results['results']

                    cols_per_row = 3
                    for i in range(0, len(products), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col in enumerate(cols):
                            if i + j < len(products):
                                display_product_card(products[i + j], col)
                else:
                    st.warning("No results found")

    # Analytics Dashboard (if requested)
    if st.session_state.get('show_analytics', False):
        st.markdown("---")
        st.header("📊 Analytics Dashboard")

        stats = get_stats()
        if stats:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Queries", stats['total_queries'])

            with col2:
                st.metric("Cache Hit Rate", f"{stats['cache_hit_rate']*100:.1f}%")

            with col3:
                st.metric("Avg Latency", f"{stats['avg_latency']*1000:.0f}ms")

            with col4:
                st.metric("Products", stats['num_products'])

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "🛍️ Multi-Modal Retail Assistant v2.0 | Powered by CLIP, FAISS & AI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
