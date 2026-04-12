from sklearn.preprocessing import StandardScaler
scaler = StandardScaler().fit_transform(X_all)  # LEAK
