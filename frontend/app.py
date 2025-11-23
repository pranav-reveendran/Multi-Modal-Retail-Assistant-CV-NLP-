"""
Streamlit Frontend for Multi-Modal Retail Assistant
Interactive UI for searching products by image or text
"""

import streamlit as st
import requests
from PIL import Image
import io
import os
from typing import List, Dict


# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")


# Page configuration
st.set_page_config(
    page_title="Multi-Modal Retail Assistant",
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
    }
    .product-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .similarity-score {
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if API is available"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def search_by_image(image_file, k=5, search_mode="image"):
    """
    Search for products using an uploaded image

    Args:
        image_file: Uploaded image file
        k: Number of results
        search_mode: Search mode ("image" or "hybrid")

    Returns:
        List of search results
    """
    try:
        files = {"file": image_file.getvalue()}
        params = {"k": k, "search_mode": search_mode}

        response = requests.post(
            f"{API_URL}/search/image",
            files={"file": image_file},
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"Error searching by image: {e}")
        return None


def search_by_text(query, k=5, search_mode="text"):
    """
    Search for products using a text query

    Args:
        query: Text search query
        k: Number of results
        search_mode: Search mode ("text" or "hybrid")

    Returns:
        List of search results
    """
    try:
        payload = {
            "query": query,
            "k": k,
            "search_mode": search_mode
        }

        response = requests.post(
            f"{API_URL}/search/text",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        st.error(f"Error searching by text: {e}")
        return None


def display_product_card(product: Dict, col):
    """
    Display a product card in the given column

    Args:
        product: Product dictionary
        col: Streamlit column to display in
    """
    with col:
        # Display image if path exists
        image_path = product.get('image_path', '')

        if os.path.exists(image_path):
            try:
                img = Image.open(image_path)
                st.image(img, use_container_width=True)
            except:
                st.info("Image not available")
        else:
            st.info("Image not available")

        # Product details
        st.markdown(f"**{product.get('title', 'N/A')}**")
        st.markdown(f"*Category:* {product.get('category', 'N/A')}")

        if 'brand' in product and product['brand']:
            st.markdown(f"*Brand:* {product['brand']}")

        if 'price' in product:
            st.markdown(f"*Price:* ${product['price']:.2f}")

        # Similarity score
        score = product.get('similarity_score', 0)
        st.markdown(
            f'<span class="similarity-score">Match: {score*100:.1f}%</span>',
            unsafe_allow_html=True
        )

        if 'description' in product and product['description']:
            with st.expander("Description"):
                st.write(product['description'])


def main():
    """Main application"""

    # Header
    st.title("🛍️ Multi-Modal Retail Assistant")
    st.markdown("### Search for products using images or text powered by CLIP")

    # Check API health
    if not check_api_health():
        st.error("⚠️ Backend API is not available. Please start the backend server:")
        st.code("cd backend && uvicorn main:app --reload")
        return

    st.success("✅ Connected to backend API")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        search_type = st.radio(
            "Search by:",
            ["Image", "Text"],
            help="Choose whether to search by uploading an image or entering text"
        )

        num_results = st.slider(
            "Number of results",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of similar products to retrieve"
        )

        search_mode = st.selectbox(
            "Search mode",
            ["image", "text", "hybrid"],
            help="Image: search in image space, Text: search in text space, Hybrid: cross-modal search"
        )

        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This app uses **CLIP** (Contrastive Language-Image Pre-training)
        to enable multi-modal product search.

        - Upload an image to find visually similar products
        - Enter text to find semantically similar items
        - Combine both for powerful cross-modal search
        """)

    # Main content area
    if search_type == "Image":
        st.header("📸 Image Search")
        st.markdown("Upload an image of a product to find similar items")

        uploaded_file = st.file_uploader(
            "Choose an image...",
            type=["jpg", "jpeg", "png"],
            help="Upload a product image"
        )

        if uploaded_file is not None:
            # Display uploaded image
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("Your Image")
                image = Image.open(uploaded_file)
                st.image(image, use_container_width=True)

            # Search button
            if st.button("🔍 Search", type="primary", use_container_width=True):
                with st.spinner("Searching for similar products..."):
                    results = search_by_image(uploaded_file, k=num_results, search_mode=search_mode)

                    if results and results.get('results'):
                        st.success(f"Found {results['num_results']} similar products!")

                        # Display results
                        st.subheader("Similar Products")

                        # Create grid layout
                        cols_per_row = 3
                        products = results['results']

                        for i in range(0, len(products), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                if i + j < len(products):
                                    display_product_card(products[i + j], col)
                    else:
                        st.warning("No results found")

    else:  # Text search
        st.header("📝 Text Search")
        st.markdown("Describe what you're looking for")

        query = st.text_input(
            "Search query",
            placeholder="e.g., 'black running shoes' or 'casual summer dress'",
            help="Enter a description of the product you're looking for"
        )

        if st.button("🔍 Search", type="primary", use_container_width=True) and query:
            with st.spinner("Searching for products..."):
                results = search_by_text(query, k=num_results, search_mode=search_mode)

                if results and results.get('results'):
                    st.success(f"Found {results['num_results']} matching products!")

                    # Display results
                    st.subheader("Matching Products")

                    # Create grid layout
                    cols_per_row = 3
                    products = results['results']

                    for i in range(0, len(products), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, col in enumerate(cols):
                            if i + j < len(products):
                                display_product_card(products[i + j], col)
                else:
                    st.warning("No results found")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Multi-Modal Retail Assistant | Powered by CLIP, FAISS, FastAPI & Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
