import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix

IMG_SIZE = 224
MODEL_PATH = "model/trash_model_best.h5"
TEST_DIR = "dataset/test"

model = tf.keras.models.load_model(MODEL_PATH)

test_gen = ImageDataGenerator(rescale=1./255)

test_data = test_gen.flow_from_directory(
    TEST_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=1,
    shuffle=False,
    class_mode="categorical"
)

print("Class Indices:", test_data.class_indices)

predictions = model.predict(test_data)
y_pred = np.argmax(predictions, axis=1)
y_true = test_data.classes

# Confusion Matrix
cm = confusion_matrix(y_true, y_pred)

print("\n📊 CONFUSION MATRIX")
print(cm)

# Classification Report
print("\n📄 CLASSIFICATION REPORT")
print(classification_report(
    y_true, y_pred,
    target_names=list(test_data.class_indices.keys())
))

# Accuracy
accuracy = np.sum(y_pred == y_true) / len(y_true)
print(f"\n🎯 Test Accuracy: {accuracy*100:.2f}%")

# Plot Confusion Matrix
plt.figure()
sns.heatmap(cm, annot=True, fmt='d',
            xticklabels=test_data.class_indices.keys(),
            yticklabels=test_data.class_indices.keys())
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.savefig("model/confusion_matrix.png")
plt.show()