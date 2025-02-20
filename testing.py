
import numpy as np

def kmeans(X, num_clusters):
    # define centroids
    # labels for each datapoint
    # new centroids
    # converge
    centroids = X[np.random.choice(X,num_clusters, replace=True)]
    
    while True:
        labels = np.argmin(np.linalg.norm(X[:,None] - centroids, axis = 2), axis =1)

        new_centroids = np.array([X[labels == i].mean(axis = 0) for i in num_clusters ])

        if np.allclose(centroids, new_centroids):
            return new_centroids
        else:
            centroids = new_centroids

def knn(X_train, X_test, y_train, k):
    # distances between train and test
    # labels count for k datapoints
    # output labels

    distances = np.sqrt(np.sum((X_train - X_test[:,None])**2))

    neighbors = np.argsort(distances)[:,:k]

    labels = y_train[neighbors]

    predicted_labels = np.apply_along_axis(lambda x: np.bincount(x).argmax(), arr=labels, axis=1)

    return predicted_labels