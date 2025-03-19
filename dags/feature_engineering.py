import pandas as pd 
import numpy as np 
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from yellowbrick.cluster import KElbowVisualizer
import matplotlib.pyplot as plt
import seaborn as sns

def scale_data(df):
    scaler = StandardScaler()
    return scaler.fit_transform(df)

def apply_pca(X_scaled, n_components=2):
    pca = PCA(n_components=n_components)
    return pca.fit_transform(X_scaled)

def find_optimal_clusters(X_pca, k_range=(2, 10)):
    model = KMeans(n_init=10, random_state=42)
    visualizer = KElbowVisualizer(model, k=k_range, metric='distortion', timings=False)
    visualizer.fit(X_pca)
    return visualizer.elbow_value_

def apply_kmeans(X_pca, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    return kmeans.fit_predict(X_pca)

def plot_clusters(X_pca, labels, k):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=X_pca[:, 0], y=X_pca[:, 1], hue=labels, palette='viridis', s=100, alpha=0.8)
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    plt.title(f'Phân cụm sản phẩm bằng PCA + K-Means (k={k})')
    plt.legend(title='Cluster')
    plt.show()

def assign_cluster_labels(df):
    cluster_summary = df.groupby("cluster")[["bought_info", "rating_count", "top"]].mean()
    print("Cluster summary:\n", cluster_summary)

    top_threshold = cluster_summary["top"].mean()  
    rating_threshold = cluster_summary["rating_count"].mean()  
    
    # Tìm các cụm thỏa mãn top > threshold và rating <= threshold
    potential_clusters = cluster_summary[
        (cluster_summary["top"] > top_threshold) & 
        (cluster_summary["rating_count"] <= rating_threshold)
    ].index.tolist()

    # So sánh bought_info trong potential_clusters
    if len(potential_clusters) > 1:
        bought_values = cluster_summary.loc[potential_clusters, "bought_info"]
        max_bought_cluster = bought_values.idxmax()
        for cluster in potential_clusters:
            if cluster == max_bought_cluster:
                df.loc[df["cluster"] == cluster, "cluster_label"] = "Potential Growth"
            else:
                df.loc[df["cluster"] == cluster, "cluster_label"] = "Steady Seller"
    elif len(potential_clusters) == 1:
        df.loc[df["cluster"] == potential_clusters[0], "cluster_label"] = "Potential Growth"

    # Gán nhãn cho các cụm còn lại
    for cluster in cluster_summary.index:
        if cluster not in potential_clusters:
            rating = cluster_summary.loc[cluster, "rating_count"]
            top = cluster_summary.loc[cluster, "top"]
            
            if top <= top_threshold:
                if rating > rating_threshold:
                    df.loc[df["cluster"] == cluster, "cluster_label"] = "Sustainable trend"
                else:
                    df.loc[df["cluster"] == cluster, "cluster_label"] = "Trending"
            else:
                if rating > rating_threshold:
                    df.loc[df["cluster"] == cluster, "cluster_label"] = "Trending again"
    
    return df

def cluster_products(df):
    X_scaled = scale_data(df)
    X_pca = apply_pca(X_scaled)
    optimal_k = find_optimal_clusters(X_pca)
    
    df['cluster'] = apply_kmeans(X_pca, optimal_k)
    plot_clusters(X_pca, df['cluster'], optimal_k)
    
    df = assign_cluster_labels(df)
    return df

if __name__ == "__main__":
    df = pd.read_csv("C:\\Users\\trong\\OneDrive\\Documents\\Project\\amazon-ecommerce\\processed.csv")
    use_df = df.drop(columns=['link', 'id', 'skin_type', 'brand', 'price', 'category'])
    clustered_df = cluster_products(use_df)
    df['cluster_label'] = clustered_df['cluster_label']
    df.to_csv("gold.csv", index=False)