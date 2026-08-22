import pandas as pd
import pickle
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(CURRENT_DIR, 'travel_destinations.csv')
PICKLE_PATH = os.path.join(CURRENT_DIR, 'destination.pkl')


def load_or_create_model():
    """Load cached ML model from pickle or create new one if cache doesn't exist"""
    
    # Check if pickle file exists
    if os.path.exists(PICKLE_PATH):
        try:
            with open(PICKLE_PATH, 'rb') as f:
                cached_data = pickle.load(f)
                return cached_data['df'], cached_data['tfidf'], cached_data['similarity']
        except Exception as e:
            print(f"Error loading pickle file: {e}. Regenerating...")
    
    # Load CSV and create model
    df = pd.read_csv(CSV_PATH)
    
    # Combine important columns
    df['tags'] = (
        df['name'] + ' ' +
        df['category'] + ' ' +
        df['description'] + ' ' +
        df['state'] + ' ' +
        df['region']
    )
    
    # TF-IDF Vectorization
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['tags'])
    
    # Cosine Similarity
    similarity = cosine_similarity(tfidf_matrix)
    
    # Cache the model
    cache_data = {
        'df': df,
        'tfidf': tfidf,
        'similarity': similarity
    }
    
    try:
        with open(PICKLE_PATH, 'wb') as f:
            pickle.dump(cache_data, f)
        print(f"ML model cached successfully to {PICKLE_PATH}")
    except Exception as e:
        print(f"Error caching model: {e}")
    
    return df, tfidf, similarity


def regenerate_cache():
    """Force regenerate the ML model cache"""
    if os.path.exists(PICKLE_PATH):
        os.remove(PICKLE_PATH)
        print(f"Removed old cache: {PICKLE_PATH}")
    
    df, tfidf, similarity = load_or_create_model()
    return df, tfidf, similarity


# Load or create model
df, tfidf, similarity = load_or_create_model()


# RECOMMEND FUNCTION

def recommend_places(user_input):

    # Convert user input into vector

    input_vector = tfidf.transform([user_input])

    # Compare with all destinations

    similarity_scores = cosine_similarity(
        input_vector,
        similarity
    )

    # Get scores

    scores = list(enumerate(similarity_scores[0]))

    # Sort scores

    sorted_scores = sorted(
        scores,
        key=lambda x: x[1],
        reverse=True
    )

    # Top 5 recommendations

    recommended = []

    for i in sorted_scores[0:5]:

        recommended.append(
            df.iloc[i[0]]['name']
        )

    return recommended